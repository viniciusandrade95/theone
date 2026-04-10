import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.http.main import create_app


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader

    monkeypatch.setattr(loader, "_config", None)
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    os.environ.setdefault("ASSISTANT_CONNECTOR_TOKEN", "test-connector-token")
    yield
    monkeypatch.setattr(loader, "_config", None)


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


def _create_service(client: TestClient, *, tenant_id: str, token: str) -> str:
    resp = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Haircut", "price_cents": 1000, "duration_minutes": 60, "is_active": True, "is_bookable_online": True},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _default_location(client: TestClient, *, tenant_id: str, token: str) -> str:
    resp = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def test_assistant_prebook_creates_and_is_idempotent():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    location_id = _default_location(client, tenant_id=tenant_id, token=token)

    starts_at = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(microsecond=0)

    payload = {
        "tenant_id": tenant_id,
        "conversation_id": str(uuid.uuid4()),
        "session_id": "session-123",
        "trace_id": "trace-xyz",
        "idempotency_key": f"{tenant_id}:conv:book_appointment:confirm",
        "customer": {"customer_id": None, "name": "Maria", "phone": "+351900000000", "email": None},
        "booking": {
            "service_id": service_id,
            "location_id": location_id,
            "starts_at": starts_at.isoformat(),
            "notes": "created via assistant",
        },
        "meta": {"surface": "dashboard", "actor_type": "staff", "source": "chatbot1"},
    }

    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Assistant-Token": "test-connector-token",
        "X-Trace-Id": "trace-header-1",
    }

    r1 = client.post("/crm/assistant/prebook", headers=headers, json=payload)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["ok"] is True
    assert body1["status"] == "created"
    assert body1["trace_id"] == "trace-xyz"
    appointment_id = body1["data"]["appointment_id"]

    r2 = client.post("/crm/assistant/prebook", headers=headers, json=payload)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["status"] == "existing"
    assert body2["data"]["appointment_id"] == appointment_id

    overview = client.get(
        "/crm/dashboard/overview",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert overview.status_code == 200
    assert overview.json()["counts"]["appointments_pending_confirmation_count"] == 1
    pending = overview.json()["sections"]["appointments_pending_confirmation"]
    assert any(item["id"] == appointment_id and item["needs_confirmation"] is True for item in pending)


def test_assistant_prebook_conflict_overlap_returns_409():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    location_id = _default_location(client, tenant_id=tenant_id, token=token)

    starts_at = (datetime.now(timezone.utc) + timedelta(hours=3)).replace(microsecond=0)
    base = {
        "tenant_id": tenant_id,
        "conversation_id": str(uuid.uuid4()),
        "session_id": "session-1",
        "idempotency_key": "k1-k1-k1-k1",
        "customer": {"customer_id": None, "name": "Ana", "phone": "+351911111111", "email": None},
        "booking": {"service_id": service_id, "location_id": location_id, "starts_at": starts_at.isoformat()},
        "meta": {"surface": "dashboard", "actor_type": "staff", "source": "chatbot1"},
    }

    headers = {"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token"}
    ok = client.post("/crm/assistant/prebook", headers=headers, json=base)
    assert ok.status_code == 200

    base2 = dict(base)
    base2["idempotency_key"] = "k2-k2-k2-k2"
    conflict = client.post("/crm/assistant/prebook", headers=headers, json=base2)
    assert conflict.status_code == 409
    assert conflict.json()["error"] == "APPOINTMENT_OVERLAP"


def test_assistant_prebook_requires_auth():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())

    resp = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "tenant_id": tenant_id,
            "idempotency_key": "k1-k1-k1-k1",
            "customer": {"customer_id": None, "name": "Maria", "phone": "+351900000000", "email": None},
            "booking": {"service_id": str(uuid.uuid4()), "starts_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()},
            "meta": {"surface": "dashboard", "actor_type": "staff", "source": "chatbot1"},
        },
    )
    assert resp.status_code == 401

