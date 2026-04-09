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
    yield
    monkeypatch.setattr(loader, "_config", None)


def _headers(tenant_id: str, token: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}


def _register(client: TestClient, tenant_id: str, email: str) -> str:
    response = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _create_customer(client: TestClient, headers: dict[str, str], idx: int) -> str:
    response = client.post(
        "/crm/customers",
        headers=headers,
        json={"name": f"Customer {idx}", "phone": f"555{idx:04d}"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _create_service(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/crm/services",
        headers=headers,
        json={"name": "Operational Service", "price_cents": 9000, "duration_minutes": 60},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_appointment_lifecycle_operational_flow():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "ops-regression@example.com")
    headers = _headers(tenant_id, token)

    location_response = client.get("/crm/locations/default", headers=headers)
    assert location_response.status_code == 200
    location_id = location_response.json()["id"]

    service_id = _create_service(client, headers)
    customer_ids = [_create_customer(client, headers, idx) for idx in range(4)]

    base = datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc)
    appointment_ids: list[str] = []
    appointment_statuses: dict[str, str] = {}

    for idx, customer_id in enumerate(customer_ids):
        starts_at = base + timedelta(hours=idx * 2)
        ends_at = starts_at + timedelta(hours=1)
        response = client.post(
            "/crm/appointments",
            headers=headers,
            json={
                "customer_id": customer_id,
                "location_id": location_id,
                "service_id": service_id,
                "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
                "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
                "status": "booked",
                "notes": f"seed-{idx}",
            },
        )
        assert response.status_code == 200
        body = response.json()
        appointment_ids.append(body["id"])
        appointment_statuses[body["id"]] = body["status"]

    completed = client.patch(
        f"/crm/appointments/{appointment_ids[0]}",
        headers=headers,
        json={"status": "completed", "notes": "client attended"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    cancelled = client.patch(
        f"/crm/appointments/{appointment_ids[1]}",
        headers=headers,
        json={"status": "cancelled", "cancelled_reason": "client_request"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelled_reason"] == "client_request"

    no_show = client.patch(
        f"/crm/appointments/{appointment_ids[2]}",
        headers=headers,
        json={"status": "no_show", "notes": "absent"},
    )
    assert no_show.status_code == 200
    assert no_show.json()["status"] == "no_show"

    rescheduled_start = base + timedelta(days=1, hours=1)
    rescheduled_end = rescheduled_start + timedelta(hours=1)
    rescheduled = client.patch(
        f"/crm/appointments/{appointment_ids[3]}",
        headers=headers,
        json={
            "starts_at": rescheduled_start.isoformat().replace("+00:00", "Z"),
            "ends_at": rescheduled_end.isoformat().replace("+00:00", "Z"),
            "status": "booked",
            "notes": "rescheduled once",
        },
    )
    assert rescheduled.status_code == 200
    assert rescheduled.json()["status"] == "booked"
    assert rescheduled.json()["starts_at"].startswith("2026-04-11T10:00:00")

    listing = client.get(
        "/crm/appointments",
        headers=headers,
        params={
            "from_dt": "2026-04-10T00:00:00Z",
            "to_dt": "2026-04-12T23:59:59Z",
            "page": 1,
            "page_size": 20,
        },
    )
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["total"] == 4

    by_id = {item["id"]: item for item in payload["items"]}
    assert by_id[appointment_ids[0]]["status"] == "completed"
    assert by_id[appointment_ids[1]]["status"] == "cancelled"
    assert by_id[appointment_ids[2]]["status"] == "no_show"
    assert by_id[appointment_ids[3]]["status"] == "booked"
    assert by_id[appointment_ids[1]]["cancelled_reason"] == "client_request"

    overview = client.get(
        "/analytics/overview",
        headers=headers,
        params={"from": "2026-04-10T00:00:00Z", "to": "2026-04-12T23:59:59Z"},
    )
    assert overview.status_code == 200
    overview_body = overview.json()
    assert overview_body["total_appointments_created"] == 4
