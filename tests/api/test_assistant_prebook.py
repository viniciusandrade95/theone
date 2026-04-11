import os
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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


def _future_date() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()


def test_prebook_forbidden():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())

    resp = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id, "Idempotency-Key": "wf:test:missing-token"},
        json={
            "customer": {"name": "Maria", "phone": "+351900000000"},
            "booking": {"service_id": str(uuid.uuid4()), "requested_date": _future_date(), "requested_time": "12:00"},
        },
    )
    assert resp.status_code == 401

    wrong = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id, "X-Assistant-Token": "wrong", "Idempotency-Key": "wf:test:401"},
        json={
            "customer": {"name": "Maria", "phone": "+351900000000"},
            "booking": {"service_id": str(uuid.uuid4()), "requested_date": _future_date(), "requested_time": "12:00"},
        },
    )
    assert wrong.status_code == 401


def test_prebook_forbidden_tenant_mismatch():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())

    resp = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:test:403"},
        json={
            "tenant_id": str(uuid.uuid4()),
            "customer": {"name": "Maria", "phone": "+351900000000"},
            "booking": {"service_id": str(uuid.uuid4()), "requested_date": _future_date(), "requested_time": "12:00"},
        },
    )
    assert resp.status_code == 403


def test_prebook_validation_error():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)
    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    _ = _default_location(client, tenant_id=tenant_id, token=token)

    resp = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:test:422"},
        json={
            "customer": {"name": "Ana", "phone": "+351911111111"},
            "booking": {
                # missing booking.service_id
                "requested_date": _future_date(),
                "requested_time": "12:00",
                "timezone": "Europe/Lisbon",
            },
        },
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "service_id" in body["details"].get("fields", {})


def test_prebook_success():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    _ = _default_location(client, tenant_id=tenant_id, token=token)

    future_date = _future_date()

    headers = {"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token"}
    payload = {
        "customer": {"name": "Maria", "phone": "+351900000000"},
        "booking": {
            "service_id": service_id,
            "requested_date": future_date,
            "requested_time": "12:00",
            "timezone": "Europe/Lisbon",
            "notes": "qualquer nota",
        },
    }

    resp = client.post(
        "/crm/assistant/prebook",
        headers={**headers, "Idempotency-Key": "wf:test:201"},
        json=payload,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert uuid.UUID(body["prebooking_id"])
    assert body["reference"] == body["prebooking_id"]
    assert body["message"] == "Pré-reserva criada com sucesso."

    expected_local = datetime.fromisoformat(f"{future_date}T12:00:00").replace(tzinfo=ZoneInfo("Europe/Lisbon"))
    expected_utc = expected_local.astimezone(timezone.utc)
    listing = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={
            "status": "pending",
            "from_dt": (expected_utc - timedelta(hours=1)).isoformat(),
            "to_dt": (expected_utc + timedelta(hours=2)).isoformat(),
        },
    )
    assert listing.status_code == 200
    item = next((row for row in listing.json()["items"] if row["id"] == body["prebooking_id"]), None)
    assert item is not None
    assert item["status"] == "pending"
    assert item["notes"].startswith("criado pelo assistant")
    assert "qualquer nota" in item["notes"]


def test_prebook_idempotent():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    _ = _default_location(client, tenant_id=tenant_id, token=token)

    future_date = _future_date()
    headers = {"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:test:idem"}
    payload = {
        "customer": {"name": "Maria", "phone": "+351900000000"},
        "booking": {"service_id": service_id, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"},
    }

    r1 = client.post("/crm/assistant/prebook", headers=headers, json=payload)
    assert r1.status_code == 201
    body1 = r1.json()

    r2 = client.post("/crm/assistant/prebook", headers=headers, json=payload)
    assert r2.status_code == 201
    assert r2.json() == body1


def test_prebook_best_effort_slot_dedupe_returns_200():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    _ = _default_location(client, tenant_id=tenant_id, token=token)

    future_date = _future_date()
    headers = {"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token"}
    payload = {
        "customer": {"name": "Maria", "phone": "+351900000000"},
        "booking": {"service_id": service_id, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"},
    }

    r1 = client.post("/crm/assistant/prebook", headers={**headers, "Idempotency-Key": "wf:test:slot-dedupe:1"}, json=payload)
    assert r1.status_code == 201
    body1 = r1.json()

    r2 = client.post("/crm/assistant/prebook", headers={**headers, "Idempotency-Key": "wf:test:slot-dedupe:2"}, json=payload)
    assert r2.status_code == 200
    assert r2.json()["prebooking_id"] == body1["prebooking_id"]


def test_prebook_conflict():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    _ = _default_location(client, tenant_id=tenant_id, token=token)

    future_date = _future_date()
    headers = {"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token"}
    base_booking = {"service_id": service_id, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"}

    ok = client.post(
        "/crm/assistant/prebook",
        headers={**headers, "Idempotency-Key": "wf:test:slot:1"},
        json={"customer": {"name": "Maria", "phone": "+351900000000"}, "booking": base_booking},
    )
    assert ok.status_code == 201

    conflict = client.post(
        "/crm/assistant/prebook",
        headers={**headers, "Idempotency-Key": "wf:test:slot:2"},
        json={"customer": {"name": "Ana", "phone": "+351911111111"}, "booking": base_booking},
    )
    assert conflict.status_code == 409
    assert conflict.json() == {"message": "Horário indisponível", "error_code": "conflict", "retriable": False}
