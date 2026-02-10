import os
import uuid

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
    yield
    monkeypatch.setattr(loader, "_config", None)


def _register(client: TestClient, tenant_id: str, email: str) -> str:
    response = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_validation_not_found_and_conflict_error_shapes():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "errors@example.com")
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}

    empty_settings_update = client.put("/crm/settings", headers=headers, json={})
    assert empty_settings_update.status_code == 400
    assert empty_settings_update.json()["error"] == "VALIDATION_ERROR"
    assert "details" in empty_settings_update.json()

    missing_customer = client.get(f"/crm/customers/{uuid.uuid4()}", headers=headers)
    assert missing_customer.status_code == 404
    assert missing_customer.json() == {"error": "NOT_FOUND"}

    customer = client.post(
        "/crm/customers",
        headers=headers,
        json={"name": "Conflict Test", "phone": "351000"},
    )
    assert customer.status_code == 200
    customer_id = customer.json()["id"]

    default_location = client.get("/crm/locations/default", headers=headers)
    assert default_location.status_code == 200
    location_id = default_location.json()["id"]

    first = client.post(
        "/crm/appointments",
        headers=headers,
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "starts_at": "2026-02-10T10:00:00Z",
            "ends_at": "2026-02-10T11:00:00Z",
        },
    )
    assert first.status_code == 200

    overlap = client.post(
        "/crm/appointments",
        headers=headers,
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "starts_at": "2026-02-10T10:30:00Z",
            "ends_at": "2026-02-10T11:30:00Z",
        },
    )
    assert overlap.status_code == 409
    body = overlap.json()
    assert body["error"] == "APPOINTMENT_OVERLAP"
    assert isinstance(body.get("conflicts"), list)
