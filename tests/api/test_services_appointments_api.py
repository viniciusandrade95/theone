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


def _create_customer(client: TestClient, tenant_id: str, token: str, name: str, phone: str) -> str:
    response = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "phone": phone},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    response = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_services_list_and_tenant_isolation():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "services-a@example.com")
    token_b = _register(client, tenant_b, "services-b@example.com")

    svc_a = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Haircut", "price_cents": 2000, "duration_minutes": 30},
    )
    assert svc_a.status_code == 200
    service_a_id = svc_a.json()["id"]
    assert svc_a.json()["is_active"] is True

    svc_a_2 = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Nails", "price_cents": 3000, "duration_minutes": 45},
    )
    assert svc_a_2.status_code == 200

    svc_b = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={"name": "Massage", "price_cents": 6000, "duration_minutes": 60},
    )
    assert svc_b.status_code == 200

    listed_a = client.get(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={"page": 1, "page_size": 5, "query": "hair", "sort": "name", "order": "asc"},
    )
    assert listed_a.status_code == 200
    body_a = listed_a.json()
    assert body_a["total"] == 1
    assert body_a["page"] == 1
    assert body_a["page_size"] == 5
    assert body_a["items"][0]["name"] == "Haircut"
    assert body_a["items"][0]["is_active"] is True

    listed_b = client.get(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
    )
    assert listed_b.status_code == 200
    body_b = listed_b.json()
    assert body_b["total"] == 1
    assert body_b["items"][0]["name"] == "Massage"

    deactivate = client.patch(
        f"/crm/services/{service_a_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"is_active": False},
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    listed_default_after_deactivate = client.get(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert listed_default_after_deactivate.status_code == 200
    names_default = {item["name"] for item in listed_default_after_deactivate.json()["items"]}
    assert "Haircut" not in names_default
    assert "Nails" in names_default

    listed_with_inactive = client.get(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={"include_inactive": True, "sort": "name", "order": "asc"},
    )
    assert listed_with_inactive.status_code == 200
    body_with_inactive = listed_with_inactive.json()
    assert body_with_inactive["total"] == 2
    by_name = {item["name"]: item for item in body_with_inactive["items"]}
    assert by_name["Haircut"]["is_active"] is False
    assert by_name["Nails"]["is_active"] is True

    tenant_b_update_other = client.patch(
        f"/crm/services/{service_a_id}",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={"name": "Should fail"},
    )
    assert tenant_b_update_other.status_code == 404

    invalid_duration = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Invalid Duration", "price_cents": 1000, "duration_minutes": 0},
    )
    assert invalid_duration.status_code == 422

    invalid_price = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Invalid Price", "price_cents": -1, "duration_minutes": 30},
    )
    assert invalid_price.status_code == 422


def test_interactions_pagination_search_and_tenant_isolation():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "interactions-a@example.com")
    token_b = _register(client, tenant_b, "interactions-b@example.com")

    customer_a = _create_customer(client, tenant_a, token_a, "Alice", "100")
    _ = _create_customer(client, tenant_b, token_b, "Bob", "200")

    add_1 = client.post(
        f"/crm/customers/{customer_a}/interactions",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"type": "note", "content": "First note"},
    )
    assert add_1.status_code == 200

    add_2 = client.post(
        f"/crm/customers/{customer_a}/interactions",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"type": "whatsapp", "content": "Ping from WhatsApp"},
    )
    assert add_2.status_code == 200

    listed = client.get(
        f"/crm/customers/{customer_a}/interactions",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={"page": 1, "page_size": 1, "query": "ping", "sort": "created_at", "order": "desc"},
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "whatsapp"

    cross_tenant = client.get(
        f"/crm/customers/{customer_a}/interactions",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
    )
    assert cross_tenant.status_code == 404


def test_appointments_status_lifecycle_and_overlap_policy():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "appointments@example.com")
    customer_id = _create_customer(client, tenant_id, token, "Maria", "351111")
    location_id = _default_location(client, tenant_id, token)

    created = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "starts_at": "2026-02-10T10:00:00Z",
            "ends_at": "2026-02-10T11:00:00Z",
            "notes": "Initial booking",
        },
    )
    assert created.status_code == 200
    first = created.json()
    assert first["status"] == "booked"
    first_id = first["id"]
    first_status_updated_at = first["status_updated_at"]

    overlap_blocked = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "starts_at": "2026-02-10T10:30:00Z",
            "ends_at": "2026-02-10T11:30:00Z",
            "notes": "Overlapping booking",
        },
    )
    assert overlap_blocked.status_code == 409
    overlap_body = overlap_blocked.json()
    assert overlap_body["error"] == "APPOINTMENT_OVERLAP"
    assert overlap_body["conflicts"][0]["id"] == first_id

    invalid_status = client.patch(
        f"/crm/appointments/{first_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"status": "invalid-status"},
    )
    assert invalid_status.status_code == 400

    cancelled = client.patch(
        f"/crm/appointments/{first_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"status": "cancelled", "cancelled_reason": "client request"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["status_updated_at"] != first_status_updated_at

    overlap_after_cancel = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "starts_at": "2026-02-10T10:30:00Z",
            "ends_at": "2026-02-10T11:30:00Z",
            "notes": "Allowed because prior one is cancelled",
        },
    )
    assert overlap_after_cancel.status_code == 200

    custom_location = client.post(
        "/crm/locations",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Second Room", "timezone": "UTC", "allow_overlaps": True},
    )
    assert custom_location.status_code == 200
    overlaps_location_id = custom_location.json()["id"]

    first_on_overlap_location = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": overlaps_location_id,
            "starts_at": "2026-02-11T09:00:00Z",
            "ends_at": "2026-02-11T10:00:00Z",
        },
    )
    assert first_on_overlap_location.status_code == 200

    second_on_overlap_location = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": overlaps_location_id,
            "starts_at": "2026-02-11T09:30:00Z",
            "ends_at": "2026-02-11T10:30:00Z",
        },
    )
    assert second_on_overlap_location.status_code == 200

    inactive_service = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Legacy Service", "price_cents": 1500, "duration_minutes": 30},
    )
    assert inactive_service.status_code == 200
    inactive_service_id = inactive_service.json()["id"]

    deactivate_service = client.patch(
        f"/crm/services/{inactive_service_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert deactivate_service.status_code == 200

    appointment_with_inactive_service = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "service_id": inactive_service_id,
            "starts_at": "2026-02-12T12:00:00Z",
            "ends_at": "2026-02-12T13:00:00Z",
        },
    )
    assert appointment_with_inactive_service.status_code == 400


def test_appointments_pagination_search_and_tenant_isolation():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "appt-a@example.com")
    token_b = _register(client, tenant_b, "appt-b@example.com")

    customer_a = _create_customer(client, tenant_a, token_a, "Ana Beatriz", "111")
    customer_a_2 = _create_customer(client, tenant_a, token_a, "Carla Dias", "333")
    customer_b = _create_customer(client, tenant_b, token_b, "Bruna", "222")
    location_a = _default_location(client, tenant_a, token_a)
    location_b = _default_location(client, tenant_b, token_b)
    service_a = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Hair Service", "price_cents": 2500, "duration_minutes": 45},
    )
    assert service_a.status_code == 200
    service_a_id = service_a.json()["id"]

    appt_a = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={
            "customer_id": customer_a,
            "location_id": location_a,
            "service_id": service_a_id,
            "starts_at": "2026-02-12T08:00:00Z",
            "ends_at": "2026-02-12T09:00:00Z",
            "notes": "Hair and makeup",
        },
    )
    assert appt_a.status_code == 200
    appointment_a_id = appt_a.json()["id"]

    appt_a_2 = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={
            "customer_id": customer_a_2,
            "location_id": location_a,
            "starts_at": "2026-02-12T10:00:00Z",
            "ends_at": "2026-02-12T11:00:00Z",
            "notes": "Second customer appointment",
        },
    )
    assert appt_a_2.status_code == 200

    appt_b = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={
            "customer_id": customer_b,
            "location_id": location_b,
            "starts_at": "2026-02-12T08:00:00Z",
            "ends_at": "2026-02-12T09:00:00Z",
            "notes": "B tenant appointment",
        },
    )
    assert appt_b.status_code == 200

    listed = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={
            "page": 1,
            "page_size": 10,
            "query": "ana",
            "from_dt": "2026-02-01T00:00:00Z",
            "to_dt": "2026-02-20T00:00:00Z",
            "sort": "starts_at",
            "order": "asc",
        },
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == appointment_a_id

    by_customer = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={
            "page": 1,
            "page_size": 10,
            "from_dt": "2026-02-01T00:00:00Z",
            "to_dt": "2026-02-20T00:00:00Z",
            "customer_id": customer_a,
        },
    )
    assert by_customer.status_code == 200
    customer_body = by_customer.json()
    assert customer_body["total"] == 1
    assert customer_body["items"][0]["customer_id"] == customer_a

    by_status = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={
            "page": 1,
            "page_size": 10,
            "from_dt": "2026-02-01T00:00:00Z",
            "to_dt": "2026-02-20T00:00:00Z",
            "status": "booked",
        },
    )
    assert by_status.status_code == 200
    assert by_status.json()["total"] == 2

    by_service = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={
            "page": 1,
            "page_size": 10,
            "from_dt": "2026-02-01T00:00:00Z",
            "to_dt": "2026-02-20T00:00:00Z",
            "service_id": service_a_id,
        },
    )
    assert by_service.status_code == 200
    assert by_service.json()["total"] == 1
    assert by_service.json()["items"][0]["id"] == appointment_a_id

    missing_range = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={"page": 1, "page_size": 10},
    )
    assert missing_range.status_code == 422


def test_calendar_endpoint_returns_denormalized_items_and_tenant_isolation():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "calendar-a@example.com")
    token_b = _register(client, tenant_b, "calendar-b@example.com")

    customer_a = _create_customer(client, tenant_a, token_a, "Alice Calendar", "555111")
    customer_b = _create_customer(client, tenant_b, token_b, "Bob Calendar", "555222")
    location_a = _default_location(client, tenant_a, token_a)
    location_b = _default_location(client, tenant_b, token_b)

    service_a = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Calendar Haircut", "price_cents": 8000, "duration_minutes": 60},
    )
    assert service_a.status_code == 200
    service_a_id = service_a.json()["id"]

    appt_a = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={
            "customer_id": customer_a,
            "location_id": location_a,
            "service_id": service_a_id,
            "starts_at": "2026-02-17T09:00:00Z",
            "ends_at": "2026-02-17T10:00:00Z",
            "notes": "Calendar endpoint appointment",
        },
    )
    assert appt_a.status_code == 200
    appt_a_id = appt_a.json()["id"]

    appt_b = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={
            "customer_id": customer_b,
            "location_id": location_b,
            "starts_at": "2026-02-17T09:30:00Z",
            "ends_at": "2026-02-17T10:30:00Z",
        },
    )
    assert appt_b.status_code == 200

    calendar = client.get(
        "/crm/calendar",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        params={
            "from_dt": "2026-02-17T00:00:00Z",
            "to_dt": "2026-02-18T00:00:00Z",
            "location_id": location_a,
        },
    )
    assert calendar.status_code == 200
    items = calendar.json()["items"]
    assert len(items) == 1
    item = items[0]
    assert item["id"] == appt_a_id
    assert item["location_id"] == location_a
    assert item["status"] == "booked"
    assert item["customer"]["id"] == customer_a
    assert item["customer"]["name"] == "Alice Calendar"
    assert item["customer"]["phone"] == "555111"
    assert item["service"]["id"] == service_a_id
    assert item["service"]["name"] == "Calendar Haircut"
    assert item["service"]["duration_min"] == 60
    assert item["service"]["price"] == 80.0

    cross_tenant = client.get(
        "/crm/calendar",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        params={
            "from_dt": "2026-02-17T00:00:00Z",
            "to_dt": "2026-02-18T00:00:00Z",
            "location_id": location_a,
        },
    )
    assert cross_tenant.status_code == 200
    assert cross_tenant.json()["items"] == []

    tenant_b_update_other = client.patch(
        f"/crm/appointments/{appt_a_id}",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={"notes": "should fail"},
    )
    assert tenant_b_update_other.status_code == 404
