import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.http.main import create_app
from core.db.session import db_session
from core.observability.metrics import reset_metrics
from modules.assistant.models.funnel_event_orm import AssistantFunnelEventORM
from modules.assistant.models.handoff_orm import AssistantHandoffORM
from modules.crm.models.interaction_orm import InteractionORM
from modules.messaging.models.outbound_delivery_event_orm import OutboundDeliveryEventORM
from modules.messaging.models.outbound_message_orm import OutboundMessageORM


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader

    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "dev")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    os.environ.setdefault("ASSISTANT_CONNECTOR_TOKEN", "test-connector-token")
    os.environ.setdefault("CHATBOT_SERVICE_BASE_URL", "http://chatbot.local")
    os.environ.setdefault("CHATBOT_SERVICE_TIMEOUT_SECONDS", "5")
    os.environ.setdefault("WHATSAPP_WEBHOOK_SECRET", "wh-secret")
    os.environ.setdefault("WHATSAPP_CLOUD_ACCESS_TOKEN", "token")
    os.environ.setdefault("WHATSAPP_CLOUD_API_VERSION", "v19.0")
    os.environ.setdefault("WHATSAPP_CLOUD_TIMEOUT_SECONDS", "3")
    os.environ.setdefault("SMTP_HOST", "smtp.local")
    os.environ.setdefault("SMTP_FROM", "noreply@example.com")
    yield
    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()


def _register_and_login(client: TestClient, tenant_id: str) -> str:
    client.post("/auth/register", headers={"X-Tenant-ID": tenant_id}, json={"email": f"{tenant_id}@example.com", "password": "secret123"})
    login = client.post("/auth/login", headers={"X-Tenant-ID": tenant_id}, json={"email": f"{tenant_id}@example.com", "password": "secret123"})
    return login.json()["token"]


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    r = client.get("/crm/locations/default", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    return r.json()["id"]


def _create_service(client: TestClient, tenant_id: str, token: str) -> str:
    r = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Haircut", "price_cents": 1000, "duration_minutes": 30, "is_active": True, "is_bookable_online": True},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _create_customer(client: TestClient, tenant_id: str, token: str, *, name: str, phone: str, email: str | None = None) -> str:
    payload = {"name": name, "phone": phone}
    if email:
        payload["email"] = email
    r = client.post("/crm/customers", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}, json=payload)
    assert r.status_code == 200
    return r.json()["id"]


def _create_template(client: TestClient, tenant_id: str, token: str, *, t_type: str, channel: str, body: str, name: str) -> str:
    tpl = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "type": t_type, "channel": channel, "body": body, "is_active": True},
    )
    assert tpl.status_code == 200
    return tpl.json()["id"]


def _create_whatsapp_account(client: TestClient, tenant_id: str, token: str, *, phone_number_id: str) -> None:
    r = client.post(
        "/messaging/whatsapp-accounts",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"provider": "meta", "phone_number_id": phone_number_id, "status": "active"},
    )
    assert r.status_code == 200


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _now_range() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    return (now - timedelta(hours=1)).isoformat(), (now + timedelta(hours=1)).isoformat()


def test_prebook_confirmation_delivery_and_roi_analytics(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    token_a = _register_and_login(client, tenant_a)
    service_id = _create_service(client, tenant_a, token_a)
    _ = _default_location(client, tenant_a, token_a)

    _create_whatsapp_account(client, tenant_a, token_a, phone_number_id="pn-a")
    _create_template(
        client,
        tenant_a,
        token_a,
        t_type="assistant_prebook_confirmation",
        channel="whatsapp",
        name="Assistant Prebook Confirmation",
        body="Olá {{customer_name}}! Pré-reserva para {{service_name}} em {{appointment_date}} às {{appointment_time}}.",
    )

    # Deterministic provider send.
    def fake_post(url, json, headers, timeout):
        assert url.endswith("/pn-a/messages")
        return DummyResponse({"messages": [{"id": "wamid.auto.1"}]})

    monkeypatch.setattr("modules.messaging.providers.meta_whatsapp_cloud.requests.post", fake_post)

    future_date = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()
    prebook = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_a, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:int:001"},
        json={
            "customer": {"name": "Alice", "phone": "+351900000000"},
            "booking": {"service_id": service_id, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"},
        },
    )
    assert prebook.status_code == 201
    appointment_id = prebook.json()["data"]["appointment_id"]

    with db_session() as session:
        msg = session.execute(
            select(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_a))
            .where(OutboundMessageORM.trigger_type == "assistant_prebook_created")
            .where(OutboundMessageORM.appointment_id == uuid.UUID(appointment_id))
        ).scalar_one()
        assert msg.status == "sent"
        assert msg.delivery_status == "accepted"
        assert msg.provider == "meta"
        assert msg.provider_message_id == "wamid.auto.1"

        # Funnel events were emitted and are deduped across retries.
        events = session.execute(
            select(AssistantFunnelEventORM.event_name)
            .where(AssistantFunnelEventORM.tenant_id == uuid.UUID(tenant_a))
        ).scalars().all()
        assert "assistant_prebook_requested" in events
        assert "assistant_prebook_created" in events

    # Wrong-tenant callback should not update the message (tenant safe routing by phone_number_id).
    tenant_b = str(uuid.uuid4())
    token_b = _register_and_login(client, tenant_b)
    _create_whatsapp_account(client, tenant_b, token_b, phone_number_id="pn-b")
    payload = {
        "provider": "meta",
        "external_event_id": "evt-wrong-tenant",
        "phone_number_id": "pn-b",
        "provider_message_id": "wamid.auto.1",
        "channel": "whatsapp",
        "status": "delivered",
        "payload": {"status": "delivered"},
    }
    import json as _json

    raw = _json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature = _sign("wh-secret", raw)
    cb_wrong = client.post("/messaging/delivery", data=raw, headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature})
    assert cb_wrong.status_code == 200
    assert cb_wrong.json()["updated_message_id"] is None

    # Correct callback delivered + duplicate handling.
    payload["external_event_id"] = "evt-1"
    payload["phone_number_id"] = "pn-a"
    raw2 = _json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature2 = _sign("wh-secret", raw2)
    cb = client.post("/messaging/delivery", data=raw2, headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature2})
    assert cb.status_code == 200
    assert cb.json()["recorded"] is True
    cb_dup = client.post("/messaging/delivery", data=raw2, headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature2})
    assert cb_dup.status_code == 200
    assert cb_dup.json()["recorded"] is False

    with db_session() as session:
        msg = session.execute(
            select(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_a))
            .where(OutboundMessageORM.trigger_type == "assistant_prebook_created")
            .where(OutboundMessageORM.appointment_id == uuid.UUID(appointment_id))
        ).scalar_one()
        assert msg.delivery_status in {"delivered", "read"}
        assert msg.status == "delivered"
        events = session.execute(select(OutboundDeliveryEventORM).where(OutboundDeliveryEventORM.tenant_id == uuid.UUID(tenant_a))).scalars().all()
        assert len(events) == 1

    # Duplicate trigger: same idempotency key should not create a new confirmation/outbound.
    again = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_a, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:int:001"},
        json={
            "customer": {"name": "Alice", "phone": "+351900000000"},
            "booking": {"service_id": service_id, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"},
        },
    )
    assert again.status_code == 200
    with db_session() as session:
        msgs = session.execute(
            select(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_a))
            .where(OutboundMessageORM.trigger_type == "assistant_prebook_created")
        ).scalars().all()
        assert len(msgs) == 1

    # Conversion confirmed: pending -> booked emits assistant_conversion_confirmed.
    upd = client.patch(
        f"/crm/appointments/{appointment_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"status": "booked"},
    )
    assert upd.status_code == 200

    start, end = _now_range()
    overview = client.get(
        "/analytics/assistant/overview",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={"from": start, "to": end},
    )
    assert overview.status_code == 200
    data = overview.json()
    assert data["prebook"]["created"] == 1
    assert data["conversion"]["confirmed"] == 1
    assert any(i["channel"] == "whatsapp" for i in data["outbound"])


def test_handoff_confirmation_flow_and_analytics(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)
    _ = _default_location(client, tenant_id, token)
    customer_id = _create_customer(client, tenant_id, token, name="Bob", phone="123", email="bob@example.com")

    # Set both templates: WhatsApp will fail (no account configured) and fall back to email.
    _create_template(
        client,
        tenant_id,
        token,
        t_type="assistant_handoff_confirmation",
        channel="whatsapp",
        name="Handoff WA",
        body="Olá {{customer_name}}! Pedido de atendente recebido.",
    )
    _create_template(
        client,
        tenant_id,
        token,
        t_type="assistant_handoff_confirmation",
        channel="email",
        name="Handoff Email",
        body="Olá {{customer_name}}! Pedido de atendente recebido.",
    )

    from modules.messaging.providers.outbound_provider import OutboundSendResult

    def fake_send_email_text(self, *, to_email, subject, body, trace_id, idempotency_key=None):
        return OutboundSendResult(provider="smtp", provider_message_id="email.auto.1")

    monkeypatch.setattr("modules.messaging.providers.smtp_email.SmtpEmailProvider.send_email_text", fake_send_email_text)

    def fake_chatbot_post(url, json, headers, timeout):
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

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_chatbot_post)

    first = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Quero falar com um atendente", "surface": "dashboard", "customer_id": customer_id},
    )
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]

    with db_session() as session:
        # Handoff record + CRM interaction exist.
        handoffs = session.execute(select(AssistantHandoffORM).where(AssistantHandoffORM.tenant_id == uuid.UUID(tenant_id))).scalars().all()
        assert len(handoffs) == 1
        interactions = session.execute(
            select(InteractionORM)
            .where(InteractionORM.tenant_id == uuid.UUID(tenant_id))
            .where(InteractionORM.customer_id == uuid.UUID(customer_id))
            .where(InteractionORM.type == "assistant_handoff")
        ).scalars().all()
        assert len(interactions) == 1

        # Confirmations: failed WhatsApp attempt + successful email fallback.
        msgs = session.execute(
            select(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id))
            .where(OutboundMessageORM.trigger_type == "assistant_handoff_created")
        ).scalars().all()
        assert any(m.channel == "whatsapp" and m.status == "failed" for m in msgs)
        assert any(m.channel == "email" and m.status == "sent" for m in msgs)

    # Duplicate handoff intent in same conversation should not create new handoffs or confirmations.
    second = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Preciso de um humano", "surface": "dashboard", "conversation_id": conversation_id},
    )
    assert second.status_code == 200

    with db_session() as session:
        handoffs2 = session.execute(select(AssistantHandoffORM).where(AssistantHandoffORM.tenant_id == uuid.UUID(tenant_id))).scalars().all()
        assert len(handoffs2) == 1
        msgs2 = session.execute(
            select(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id))
            .where(OutboundMessageORM.trigger_type == "assistant_handoff_created")
        ).scalars().all()
        assert len(msgs2) == 2

    start, end = _now_range()
    overview = client.get(
        "/analytics/assistant/overview",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"from": start, "to": end},
    )
    assert overview.status_code == 200
    data = overview.json()
    assert data["messages"]["received"] >= 2
    assert data["handoff"]["created"] == 1

