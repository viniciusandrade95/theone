import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.http.main import create_app
from core.db.session import db_session
from core.observability.metrics import reset_metrics
from modules.assistant.models.handoff_orm import AssistantHandoffORM
from modules.chatbot.models.conversation_message_orm import ChatbotConversationMessageORM
from modules.chatbot.models.conversation_session_orm import ChatbotConversationSessionORM
from modules.crm.models.interaction_orm import InteractionORM


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader

    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    os.environ["CHATBOT_SERVICE_BASE_URL"] = "http://chatbot.local"
    os.environ["CHATBOT_SERVICE_TIMEOUT_SECONDS"] = "5"
    yield
    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()


def _register_and_login(client: TestClient, tenant_id: str) -> str:
    client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{tenant_id}@example.com", "password": "secret123"},
    )
    login = client.post(
        "/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{tenant_id}@example.com", "password": "secret123"},
    )
    return login.json()["token"]


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    r = client.get("/crm/locations/default", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    return r.json()["id"]


def _update_default_location_hours(client: TestClient, tenant_id: str, token: str, *, timezone_name: str, hours_json: dict):
    r = client.put(
        "/crm/settings/location",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"timezone": timezone_name, "hours_json": hours_json},
    )
    assert r.status_code == 200


def _create_service(client: TestClient, tenant_id: str, token: str, *, name: str, duration: int = 30, price_cents: int = 1000) -> str:
    r = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "price_cents": price_cents, "duration_minutes": duration},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _set_service_bookable(client: TestClient, tenant_id: str, token: str, service_id: str, *, is_bookable: bool):
    r = client.patch(
        f"/crm/services/{service_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"is_bookable_online": is_bookable},
    )
    assert r.status_code == 200


def _enable_booking(client: TestClient, tenant_id: str, token: str, *, slug: str, business_name: str, min_notice: int = 0, max_days: int = 30):
    r = client.put(
        "/crm/booking/settings",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "booking_enabled": True,
            "booking_slug": slug,
            "public_business_name": business_name,
            "min_booking_notice_minutes": min_notice,
            "max_booking_notice_days": max_days,
            "auto_confirm_bookings": True,
        },
    )
    assert r.status_code == 200


def _create_customer(client: TestClient, tenant_id: str, token: str, *, name: str, phone: str) -> str:
    r = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "phone": phone},
    )
    assert r.status_code == 200
    return r.json()["id"]


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_e2e_assistant_slot_suggestions_multi_turn(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    location_id = _default_location(client, tenant_id, token)
    _update_default_location_hours(
        client,
        tenant_id,
        token,
        timezone_name="Europe/Dublin",
        hours_json={
            "mon": {"open": "09:00", "close": "18:00"},
            "tue": {"open": "09:00", "close": "18:00"},
            "wed": {"open": "09:00", "close": "18:00"},
            "thu": {"open": "09:00", "close": "18:00"},
            "fri": {"open": "09:00", "close": "18:00"},
            "sat": {"open": "09:00", "close": "18:00"},
            "sun": {"open": "09:00", "close": "18:00"},
        },
    )

    service_id = _create_service(client, tenant_id, token, name="Haircut", duration=30)
    _set_service_bookable(client, tenant_id, token, service_id, is_bookable=True)
    _enable_booking(client, tenant_id, token, slug="assistant-slots", business_name="Assistant Slots", min_notice=0, max_days=30)

    target_date = (datetime.now(timezone.utc) + timedelta(days=7)).date().isoformat()

    # Seed an occupied slot to ensure we are using the real availability engine.
    availability = client.get(
        "/public/book/assistant-slots/availability",
        params={"service_id": service_id, "date": target_date, "location_id": location_id},
    )
    assert availability.status_code == 200
    all_slots = availability.json()["slots"]
    assert len(all_slots) > 5
    occupied = all_slots[0]
    customer_id = _create_customer(client, tenant_id, token, name="Alice", phone="351111")
    r = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": occupied["starts_at"],
            "ends_at": occupied["ends_at"],
            "status": "booked",
        },
    )
    assert r.status_code == 200

    calls = {"n": 0}

    def fake_post(url, json, headers, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            return DummyResponse(
                {
                    "status": "ok",
                    "reply": "ok",
                    "session_id": "s-123",
                    "intent": "find_slots",
                    "slots": {"requested_date": target_date},
                }
            )
        return DummyResponse(
            {
                "status": "ok",
                "reply": "ok",
                "session_id": "s-123",
                "intent": "find_slots",
                "slots": {"service_id": service_id},
            }
        )

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    turn1 = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Quero marcar um horário", "surface": "dashboard"},
    )
    assert turn1.status_code == 200
    b1 = turn1.json()
    assert b1["intent"] == "find_slots"
    assert "Para que serviço" in b1["reply"]["text"]
    assert any(a.get("type") == "assistant.slot_suggestions.v1" and a.get("outcome") == "missing_info" for a in b1["reply"]["actions"])

    turn2 = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Haircut", "surface": "dashboard", "conversation_id": b1["conversation_id"]},
    )
    assert turn2.status_code == 200
    b2 = turn2.json()
    actions = [a for a in b2["reply"]["actions"] if a.get("type") == "assistant.slot_suggestions.v1"]
    assert actions
    action = actions[-1]
    assert action["outcome"] == "success"
    assert 3 <= len(action["slots"]) <= 5
    # Should match the public booking availability source-of-truth (after occupied slot is removed).
    availability2 = client.get(
        "/public/book/assistant-slots/availability",
        params={"service_id": service_id, "date": target_date, "location_id": location_id},
    )
    assert availability2.status_code == 200
    expected = availability2.json()["slots"][: len(action["slots"])]
    assert [s["starts_at"] for s in action["slots"]] == [s["starts_at"] for s in expected]

    # Continuity: persisted booking state and history exist.
    conversation_id = b2["conversation_id"]
    with db_session() as session:
        conv = session.execute(
            select(ChatbotConversationSessionORM).where(ChatbotConversationSessionORM.conversation_id == uuid.UUID(conversation_id))
        ).scalar_one()
        assert conv.last_intent == "find_slots"
        assert isinstance(conv.state_payload, dict)
        assert conv.state_payload.get("booking", {}).get("service_id")
        assert conv.state_payload.get("booking", {}).get("requested_date") == target_date
        assert isinstance(conv.context_payload, dict)
        assert isinstance(conv.context_payload.get("last_slot_suggestions"), list)

        msgs = session.execute(
            select(ChatbotConversationMessageORM).where(ChatbotConversationMessageORM.conversation_id == uuid.UUID(conversation_id))
        ).scalars().all()
        # 2 user + 2 assistant messages
        assert len(msgs) >= 4


def test_e2e_assistant_handoff_creates_record_and_interaction(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    _default_location(client, tenant_id, token)
    customer_id = _create_customer(client, tenant_id, token, name="Bob", phone="999")

    def fake_post(url, json, headers, timeout):
        return DummyResponse(
            {
                "status": "ok",
                "reply": "ok",
                "session_id": "s-123",
                "intent": "handoff",
                "handoff_requested": True,
                "handoff_reason": "user_requested_human",
            }
        )

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    first = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Quero falar com um atendente", "surface": "dashboard", "customer_id": customer_id},
    )
    assert first.status_code == 200
    body = first.json()
    assert body["handoff"]["requested"] is True
    assert "atendente humano" in body["reply"]["text"].lower()
    actions = body["reply"]["actions"]
    assert any(a.get("type") == "assistant.handoff.v1" for a in actions)
    handoff_id = next(a.get("handoff_id") for a in actions if a.get("type") == "assistant.handoff.v1")

    # Internal visibility path.
    listed = client.get(
        "/crm/assistant/handoffs",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert any(i["id"] == handoff_id for i in listed.json()["items"])

    # Real backend side effects.
    with db_session() as session:
        rows = session.execute(select(AssistantHandoffORM)).scalars().all()
        assert len(rows) == 1
        assert str(rows[0].tenant_id) == tenant_id
        assert str(rows[0].customer_id) == customer_id
        assert str(rows[0].id) == handoff_id

        interactions = session.execute(
            select(InteractionORM)
            .where(InteractionORM.tenant_id == uuid.UUID(tenant_id))
            .where(InteractionORM.customer_id == uuid.UUID(customer_id))
            .where(InteractionORM.type == "assistant_handoff")
        ).scalars().all()
        assert len(interactions) == 1
        assert interactions[0].payload.get("handoff_id") == handoff_id

    # Repeated request in same conversation should not create duplicates.
    second = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Preciso de um humano", "surface": "dashboard", "conversation_id": body["conversation_id"]},
    )
    assert second.status_code == 200
    with db_session() as session:
        rows = session.execute(select(AssistantHandoffORM)).scalars().all()
        assert len(rows) == 1

