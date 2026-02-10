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
    register = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "secret123"},
    )
    assert register.status_code == 200
    return register.json()["token"]


def _login(client: TestClient, tenant_id: str, email: str) -> str:
    login = client.post(
        "/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "secret123"},
    )
    assert login.status_code == 200
    return login.json()["token"]


def test_locations_crud_and_tenant_isolation():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "a@example.com")
    token_b = _register(client, tenant_b, "b@example.com")

    created = client.post(
        "/crm/locations",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Downtown", "timezone": "America/New_York"},
    )
    assert created.status_code == 200
    location_id = created.json()["id"]
    assert created.json()["name"] == "Downtown"
    assert created.json()["timezone"] == "America/New_York"

    fetched = client.get(
        f"/crm/locations/{location_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert fetched.status_code == 200

    forbidden = client.get(
        f"/crm/locations/{location_id}",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
    )
    assert forbidden.status_code == 404

    updated = client.put(
        f"/crm/locations/{location_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Downtown HQ", "allow_overlaps": True},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Downtown HQ"
    assert updated.json()["allow_overlaps"] is True

    deleted = client.delete(
        f"/crm/locations/{location_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert deleted.status_code == 200

    listed_default = client.get(
        "/crm/locations",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert listed_default.status_code == 200
    assert all(item["id"] != location_id for item in listed_default.json()["items"])

    listed_with_deleted = client.get(
        "/crm/locations",
        params={"include_deleted": "true", "include_inactive": "true"},
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert listed_with_deleted.status_code == 200
    deleted_item = next((item for item in listed_with_deleted.json()["items"] if item["id"] == location_id), None)
    assert deleted_item is not None
    assert deleted_item["deleted_at"] is not None


def test_default_location_is_recreated_on_login_when_missing():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    email = "login-default@example.com"
    token = _register(client, tenant_id, email)

    default_before = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert default_before.status_code == 200
    first_location_id = default_before.json()["id"]

    deleted = client.delete(
        f"/crm/locations/{first_location_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 200

    token_after_login = _login(client, tenant_id, email)
    default_after = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token_after_login}"},
    )
    assert default_after.status_code == 200
    assert default_after.json()["id"] != first_location_id


def test_appointments_require_location_id():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "appt@example.com")

    customer = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Maria", "phone": "351111"},
    )
    assert customer.status_code == 200
    customer_id = customer.json()["id"]

    missing_location = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "starts_at": "2026-02-10T10:00:00Z",
            "ends_at": "2026-02-10T11:00:00Z",
            "status": "booked",
        },
    )
    assert missing_location.status_code == 422

    default_location = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert default_location.status_code == 200
    location_id = default_location.json()["id"]

    created = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "service_id": None,
            "starts_at": "2026-02-10T10:00:00Z",
            "ends_at": "2026-02-10T11:00:00Z",
            "status": "booked",
        },
    )
    assert created.status_code == 200
    assert created.json()["location_id"] == location_id


def test_location_timezone_validation():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "tz@example.com")

    bad = client.post(
        "/crm/locations",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Invalid TZ", "timezone": "Mars/Olympus"},
    )
    assert bad.status_code == 422
