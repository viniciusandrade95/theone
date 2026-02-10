import os
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.http.main import create_app
from core.db.session import db_session
from modules.crm.models.customer_orm import CustomerORM


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


def _create_customer(client: TestClient, tenant_id: str, token: str, name: str, phone: str) -> str:
    response = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "phone": phone},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _create_service(client: TestClient, tenant_id: str, token: str, name: str) -> str:
    response = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "price_cents": 5000, "duration_minutes": 60},
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


def _create_appointment(
    client: TestClient,
    tenant_id: str,
    token: str,
    *,
    customer_id: str,
    location_id: str,
    starts_at: str,
    ends_at: str,
    service_id: str | None = None,
):
    response = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "status": "booked",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _set_appointment_status(client: TestClient, tenant_id: str, token: str, appointment_id: str, status: str):
    payload = {"status": status}
    if status == "cancelled":
        payload["cancelled_reason"] = "client request"
    response = client.patch(
        f"/crm/appointments/{appointment_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200


def _set_customer_created_at(customer_id: str, target_dt: datetime):
    with db_session() as session:
        stmt = select(CustomerORM).where(CustomerORM.id == uuid.UUID(customer_id))
        customer = session.execute(stmt).scalar_one()
        customer.created_at = target_dt
        session.flush()


def test_analytics_endpoints_overview_services_heatmap_and_at_risk():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "analytics@example.com")

    customer_new = _create_customer(client, tenant_id, token, "Alice", "100")
    customer_old = _create_customer(client, tenant_id, token, "Bruna", "200")
    _set_customer_created_at(customer_new, datetime(2026, 2, 5, 9, 0, tzinfo=timezone.utc))
    _set_customer_created_at(customer_old, datetime(2025, 12, 20, 9, 0, tzinfo=timezone.utc))

    service_hair = _create_service(client, tenant_id, token, "Hair")
    service_nails = _create_service(client, tenant_id, token, "Nails")
    location_id = _default_location(client, tenant_id, token)

    update_settings = client.put(
        "/crm/settings",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"default_timezone": "America/New_York"},
    )
    assert update_settings.status_code == 200

    a1 = _create_appointment(
        client,
        tenant_id,
        token,
        customer_id=customer_new,
        location_id=location_id,
        service_id=service_hair,
        starts_at="2026-02-10T10:00:00Z",
        ends_at="2026-02-10T11:00:00Z",
    )
    a2 = _create_appointment(
        client,
        tenant_id,
        token,
        customer_id=customer_new,
        location_id=location_id,
        service_id=service_hair,
        starts_at="2026-02-11T12:00:00Z",
        ends_at="2026-02-11T13:00:00Z",
    )
    a3 = _create_appointment(
        client,
        tenant_id,
        token,
        customer_id=customer_old,
        location_id=location_id,
        service_id=service_nails,
        starts_at="2026-02-12T14:00:00Z",
        ends_at="2026-02-12T15:00:00Z",
    )
    a4 = _create_appointment(
        client,
        tenant_id,
        token,
        customer_id=customer_old,
        location_id=location_id,
        starts_at="2026-02-13T16:00:00Z",
        ends_at="2026-02-13T17:00:00Z",
    )
    _create_appointment(
        client,
        tenant_id,
        token,
        customer_id=customer_old,
        location_id=location_id,
        service_id=service_nails,
        starts_at="2026-01-05T09:00:00Z",
        ends_at="2026-01-05T10:00:00Z",
    )

    _set_appointment_status(client, tenant_id, token, a2, "completed")
    _set_appointment_status(client, tenant_id, token, a3, "cancelled")
    _set_appointment_status(client, tenant_id, token, a4, "no_show")

    params = {
        "from": "2026-02-01T00:00:00Z",
        "to": "2026-03-01T00:00:00Z",
    }

    overview = client.get(
        "/analytics/overview",
        params=params,
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert overview.status_code == 200
    overview_body = overview.json()
    assert overview_body["total_appointments_created"] == 4
    assert overview_body["completed_count"] == 1
    assert overview_body["cancelled_count"] == 1
    assert overview_body["no_show_count"] == 1
    assert overview_body["new_customers"] == 1
    assert overview_body["returning_customers"] == 1
    assert overview_body["repeat_rate"] == pytest.approx(0.5)

    services = client.get(
        "/analytics/services",
        params=params,
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert services.status_code == 200
    services_body = services.json()
    assert services_body["total_bookings"] == 4
    by_name = {item["service_name"]: item for item in services_body["service_mix"]}
    assert by_name["Hair"]["bookings"] == 2
    assert by_name["Nails"]["bookings"] == 1
    assert by_name["Unassigned"]["bookings"] == 1

    heatmap = client.get(
        "/analytics/heatmap",
        params=params,
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert heatmap.status_code == 200
    heatmap_body = heatmap.json()
    assert heatmap_body["timezone"] == "America/New_York"
    counts = {(item["weekday"], item["hour"]): item["count"] for item in heatmap_body["items"]}
    assert counts[("tue", 5)] == 1
    assert counts[("wed", 7)] == 1
    assert counts[("thu", 9)] == 1
    assert counts[("fri", 11)] == 1

    bookings = client.get(
        "/analytics/bookings_over_time",
        params=params,
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert bookings.status_code == 200
    by_date = {item["date"]: item["count"] for item in bookings.json()["items"]}
    assert by_date["2026-02-10"] == 1
    assert by_date["2026-02-11"] == 1
    assert by_date["2026-02-12"] == 1
    assert by_date["2026-02-13"] == 1

    at_risk = client.get(
        "/analytics/at_risk",
        params={**params, "threshold_days": 14},
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert at_risk.status_code == 200
    assert at_risk.json()["threshold_days"] == 14
    assert len(at_risk.json()["items"]) == 2


def test_analytics_location_filter():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "analytics-location@example.com")
    customer_id = _create_customer(client, tenant_id, token, "Carol", "300")
    service_id = _create_service(client, tenant_id, token, "Spa")
    default_location = _default_location(client, tenant_id, token)

    second_location = client.post(
        "/crm/locations",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Second Room", "timezone": "UTC"},
    )
    assert second_location.status_code == 200
    second_location_id = second_location.json()["id"]

    _create_appointment(
        client,
        tenant_id,
        token,
        customer_id=customer_id,
        location_id=default_location,
        service_id=service_id,
        starts_at="2026-02-10T09:00:00Z",
        ends_at="2026-02-10T10:00:00Z",
    )
    _create_appointment(
        client,
        tenant_id,
        token,
        customer_id=customer_id,
        location_id=second_location_id,
        service_id=service_id,
        starts_at="2026-02-11T09:00:00Z",
        ends_at="2026-02-11T10:00:00Z",
    )

    params = {"from": "2026-02-01T00:00:00Z", "to": "2026-03-01T00:00:00Z"}
    all_locations = client.get(
        "/analytics/overview",
        params=params,
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert all_locations.status_code == 200
    assert all_locations.json()["total_appointments_created"] == 2

    default_only = client.get(
        "/analytics/overview",
        params={**params, "location_id": default_location},
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert default_only.status_code == 200
    assert default_only.json()["total_appointments_created"] == 1

    second_only = client.get(
        "/analytics/overview",
        params={**params, "location_id": second_location_id},
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert second_only.status_code == 200
    assert second_only.json()["total_appointments_created"] == 1
