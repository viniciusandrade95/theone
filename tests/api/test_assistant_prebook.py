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


def test_assistant_prebook_requires_token():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())

    starts_at = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(microsecond=0)
    resp = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "customer": {"name": "Maria", "phone": "+351900000000"},
            "booking": {"service_id": str(uuid.uuid4()), "starts_at": starts_at.isoformat()},
        },
    )
    assert resp.status_code == 401


def test_assistant_prebook_creates_is_idempotent_and_handles_overlap():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    location_id = _default_location(client, tenant_id=tenant_id, token=token)

    starts_at = (datetime.now(timezone.utc) + timedelta(hours=2)).replace(microsecond=0)

    headers = {"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token", "X-Trace-Id": "trace-1"}
    payload = {
        "customer": {"name": "Maria", "phone": "+351900000000"},
        "booking": {"service_id": service_id, "starts_at": starts_at.isoformat()},
    }

    created = client.post("/crm/assistant/prebook", headers=headers, json=payload)
    assert created.status_code == 201
    body1 = created.json()
    assert body1["ok"] is True
    assert body1["status"] == "created"
    appointment_id = body1["data"]["appointment_id"]

    # Verify status + notes persisted.
    listing = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={
            "from_dt": (starts_at - timedelta(hours=1)).isoformat(),
            "to_dt": (starts_at + timedelta(hours=3)).isoformat(),
        },
    )
    assert listing.status_code == 200
    appt = next(item for item in listing.json()["items"] if item["id"] == appointment_id)
    assert appt["status"] == "pending"
    assert appt["notes"] == "criado pelo assistant"
    assert appt["location_id"] == location_id
    assert appt["service_id"] == service_id
    parsed_starts = datetime.fromisoformat(appt["starts_at"].replace("Z", "+00:00"))
    parsed_ends = datetime.fromisoformat(appt["ends_at"].replace("Z", "+00:00"))
    if parsed_starts.tzinfo is not None:
        parsed_starts = parsed_starts.astimezone(timezone.utc).replace(tzinfo=None)
    if parsed_ends.tzinfo is not None:
        parsed_ends = parsed_ends.astimezone(timezone.utc).replace(tzinfo=None)
    assert parsed_starts == starts_at.replace(tzinfo=None)
    assert parsed_ends == (starts_at + timedelta(minutes=60)).replace(tzinfo=None)

    existing = client.post("/crm/assistant/prebook", headers=headers, json=payload)
    assert existing.status_code == 200
    body2 = existing.json()
    assert body2["status"] == "existing"
    assert body2["data"]["appointment_id"] == appointment_id

    overlap = client.post(
        "/crm/assistant/prebook",
        headers=headers,
        json={
            "customer": {"name": "Ana", "phone": "+351911111111"},
            "booking": {"service_id": service_id, "starts_at": starts_at.isoformat()},
        },
    )
    assert overlap.status_code == 409
    assert overlap.json()["error"] == "APPOINTMENT_OVERLAP"
