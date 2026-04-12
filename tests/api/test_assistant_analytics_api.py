import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.http.main import create_app


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader
    from core.observability.metrics import reset_metrics

    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    os.environ.setdefault("ASSISTANT_CONNECTOR_TOKEN", "test-connector-token")
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


def _create_customer(client: TestClient, tenant_id: str, token: str, *, name: str, phone: str) -> str:
    r = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "phone": phone},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _create_service(client: TestClient, tenant_id: str, token: str, *, name: str = "Haircut", duration: int = 30) -> str:
    r = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "price_cents": 1000, "duration_minutes": duration, "is_active": True, "is_bookable_online": True},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    r = client.get("/crm/locations/default", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
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


def _now_range() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(minutes=10)).isoformat()
    end = (now + timedelta(minutes=10)).isoformat()
    return start, end


def test_assistant_analytics_funnel_and_isolation(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register_and_login(client, tenant_a)
    token_b = _register_and_login(client, tenant_b)

    # Seed minimal CRM entities.
    service_a = _create_service(client, tenant_a, token_a)
    _ = _default_location(client, tenant_a, token_a)
    customer_a = _create_customer(client, tenant_a, token_a, name="Alice", phone="+351900000000")

    service_b = _create_service(client, tenant_b, token_b)
    _ = _default_location(client, tenant_b, token_b)

    calls = {"n": 0}

    def fake_post(url, json, headers, timeout):
        calls["n"] += 1
        # Tenant A: first message => normal reply, second => handoff request.
        if json.get("tenant_id") == tenant_a and calls["n"] == 1:
            return DummyResponse({"status": "ok", "reply": "ok", "session_id": "s-123", "intent": "find_slots"})
        if json.get("tenant_id") == tenant_a:
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
        # Tenant B: one message.
        return DummyResponse({"status": "ok", "reply": "ok", "session_id": "s-999", "intent": "find_slots"})

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    # Tenant A: message + handoff
    m1 = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"message": "Olá", "surface": "dashboard", "customer_id": customer_a},
    )
    assert m1.status_code == 200
    conv_a = m1.json()["conversation_id"]
    m2 = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"message": "Quero um humano", "surface": "dashboard", "conversation_id": conv_a},
    )
    assert m2.status_code == 200

    # Tenant A: prebook (with idempotency) + confirm conversion via PATCH.
    future_date = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()
    pb1 = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_a, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:test:funnel"},
        json={
            "customer": {"name": "Alice", "phone": "+351900000000"},
            "booking": {"service_id": service_a, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"},
        },
    )
    assert pb1.status_code == 201
    appt_id = pb1.json()["data"]["appointment_id"]
    # Retry: idempotent hit should not increase created counts.
    pb2 = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_a, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:test:funnel"},
        json={
            "customer": {"name": "Alice", "phone": "+351900000000"},
            "booking": {"service_id": service_a, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"},
        },
    )
    assert pb2.status_code == 200

    upd = client.patch(
        f"/crm/appointments/{appt_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"status": "booked"},
    )
    assert upd.status_code == 200

    # Tenant B: one message only.
    _ = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={"message": "Olá", "surface": "dashboard"},
    )

    start, end = _now_range()
    overview_a = client.get(
        "/analytics/assistant/overview",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={"from": start, "to": end},
    )
    assert overview_a.status_code == 200
    oa = overview_a.json()
    assert oa["messages"]["received"] >= 2
    assert oa["messages"]["replied"] >= 2
    assert oa["handoff"]["created"] == 1
    assert oa["prebook"]["created"] == 1
    assert oa["conversion"]["confirmed"] == 1

    funnel_a = client.get(
        "/analytics/assistant/funnel",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={"from": start, "to": end},
    )
    assert funnel_a.status_code == 200
    stages = {i["event"]: i["count"] for i in funnel_a.json()["stages"]}
    assert stages["assistant_handoff_created"] == 1
    assert stages["assistant_prebook_created"] == 1
    assert stages["assistant_conversion_confirmed"] == 1

    # Tenant isolation: tenant B overview should not include tenant A artifacts.
    overview_b = client.get(
        "/analytics/assistant/overview",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        params={"from": start, "to": end},
    )
    assert overview_b.status_code == 200
    ob = overview_b.json()
    assert ob["messages"]["received"] >= 1
    assert ob["handoff"]["created"] == 0
    assert ob["prebook"]["created"] == 0
    assert ob["conversion"]["confirmed"] == 0

