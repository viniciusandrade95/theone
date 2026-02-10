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


def _headers(tenant_id: str, token: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    response = client.get("/crm/locations/default", headers=_headers(tenant_id, token))
    assert response.status_code == 200
    return response.json()["id"]


def test_tenant_isolation_crud_smoke_for_core_entities():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "tenant-a-smoke@example.com")
    token_b = _register(client, tenant_b, "tenant-b-smoke@example.com")
    headers_a = _headers(tenant_a, token_a)
    headers_b = _headers(tenant_b, token_b)

    # Customer A
    customer = client.post("/crm/customers", headers=headers_a, json={"name": "Tenant A Customer", "phone": "100"})
    assert customer.status_code == 200
    customer_id = customer.json()["id"]

    assert client.get(f"/crm/customers/{customer_id}", headers=headers_b).status_code == 404
    assert client.put(f"/crm/customers/{customer_id}", headers=headers_b, json={"name": "B update"}).status_code == 404
    assert client.delete(f"/crm/customers/{customer_id}", headers=headers_b).status_code == 404

    # Service A
    service = client.post(
        "/crm/services",
        headers=headers_a,
        json={"name": "Tenant A Service", "price_cents": 2500, "duration_minutes": 45},
    )
    assert service.status_code == 200
    service_id = service.json()["id"]

    assert client.patch(f"/crm/services/{service_id}", headers=headers_b, json={"name": "B update"}).status_code == 404
    assert client.delete(f"/crm/services/{service_id}", headers=headers_b).status_code == 404
    listed_b_services = client.get("/crm/services", headers=headers_b, params={"include_inactive": True})
    assert listed_b_services.status_code == 200
    assert all(item["id"] != service_id for item in listed_b_services.json()["items"])

    # Location A
    location = client.post(
        "/crm/locations",
        headers=headers_a,
        json={"name": "Tenant A Branch", "timezone": "UTC"},
    )
    assert location.status_code == 200
    location_id = location.json()["id"]

    assert client.get(f"/crm/locations/{location_id}", headers=headers_b).status_code == 404
    assert client.put(f"/crm/locations/{location_id}", headers=headers_b, json={"name": "B branch"}).status_code == 404
    assert client.delete(f"/crm/locations/{location_id}", headers=headers_b).status_code == 404

    # Appointment A
    default_location_a = _default_location(client, tenant_a, token_a)
    appointment = client.post(
        "/crm/appointments",
        headers=headers_a,
        json={
            "customer_id": customer_id,
            "service_id": service_id,
            "location_id": default_location_a,
            "starts_at": "2026-02-17T09:00:00Z",
            "ends_at": "2026-02-17T10:00:00Z",
        },
    )
    assert appointment.status_code == 200
    appointment_id = appointment.json()["id"]

    assert client.patch(f"/crm/appointments/{appointment_id}", headers=headers_b, json={"notes": "B update"}).status_code == 404
    assert client.delete(f"/crm/appointments/{appointment_id}", headers=headers_b).status_code == 404

    listed_b_appointments = client.get(
        "/crm/appointments",
        headers=headers_b,
        params={
            "from_dt": "2026-02-01T00:00:00Z",
            "to_dt": "2026-02-28T00:00:00Z",
            "location_id": default_location_a,
        },
    )
    assert listed_b_appointments.status_code == 200
    assert listed_b_appointments.json()["total"] == 0


def test_overlap_and_calendar_denormalized_smoke():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "calendar-smoke@example.com")
    headers = _headers(tenant_id, token)

    customer = client.post("/crm/customers", headers=headers, json={"name": "Calendar Person", "phone": "123"})
    assert customer.status_code == 200
    customer_id = customer.json()["id"]

    service = client.post(
        "/crm/services",
        headers=headers,
        json={"name": "Calendar Service", "price_cents": 8000, "duration_minutes": 60},
    )
    assert service.status_code == 200
    service_id = service.json()["id"]

    location_id = _default_location(client, tenant_id, token)

    first = client.post(
        "/crm/appointments",
        headers=headers,
        json={
            "customer_id": customer_id,
            "service_id": service_id,
            "location_id": location_id,
            "starts_at": "2026-02-18T10:00:00Z",
            "ends_at": "2026-02-18T11:00:00Z",
        },
    )
    assert first.status_code == 200
    first_id = first.json()["id"]

    overlap = client.post(
        "/crm/appointments",
        headers=headers,
        json={
            "customer_id": customer_id,
            "service_id": service_id,
            "location_id": location_id,
            "starts_at": "2026-02-18T10:30:00Z",
            "ends_at": "2026-02-18T11:30:00Z",
        },
    )
    assert overlap.status_code == 409
    assert overlap.json()["error"] == "APPOINTMENT_OVERLAP"
    assert overlap.json()["conflicts"][0]["id"] == first_id

    calendar = client.get(
        "/crm/calendar",
        headers=headers,
        params={
            "from_dt": "2026-02-18T00:00:00Z",
            "to_dt": "2026-02-19T00:00:00Z",
            "location_id": location_id,
        },
    )
    assert calendar.status_code == 200
    items = calendar.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["id"] == first_id
    assert item["customer"]["id"] == customer_id
    assert item["service"]["id"] == service_id
    assert item["location_id"] == location_id
