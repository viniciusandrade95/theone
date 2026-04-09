import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.http.main import create_app

TENANT = str(uuid.uuid4())
os.environ.setdefault("ENV", "test")
os.environ.setdefault("APP_NAME", "beauty-crm")
os.environ.setdefault("DATABASE_URL", "dev")
os.environ.setdefault("SECRET_KEY", "dev")
os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")


def _day_start_utc(now_utc: datetime) -> datetime:
    return datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)


def test_dashboard_overview_counts_and_lists():
    app = create_app()
    client = TestClient(app)

    # Register
    r = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": TENANT},
        json={"email": "dash@acme.com", "password": "secret123"},
    )
    assert r.status_code == 200
    token = r.json()["token"]
    auth_headers = {"X-Tenant-ID": TENANT, "Authorization": f"Bearer {token}"}

    # Force tenant timezone to UTC for deterministic "today"
    r = client.put("/crm/settings", headers=auth_headers, json={"default_timezone": "UTC"})
    assert r.status_code == 200

    # Ensure we have a location_id to use for internal appointments
    r = client.get("/crm/settings/location", headers=auth_headers)
    assert r.status_code == 200
    location_id = r.json()["id"]

    # Create a service for public bookings
    r = client.post(
        "/crm/services",
        headers=auth_headers,
        json={
            "name": "Haircut",
            "price_cents": 2500,
            "duration_minutes": 60,
            "is_active": True,
            "is_bookable_online": True,
        },
    )
    assert r.status_code == 200
    service_id = r.json()["id"]

    # Configure booking settings
    slug = "acme-studio"
    r = client.put(
        "/crm/booking/settings",
        headers=auth_headers,
        json={
            "booking_enabled": True,
            "booking_slug": slug,
            "public_business_name": "Acme Studio",
            "min_booking_notice_minutes": 0,
            "max_booking_notice_days": 90,
            "auto_confirm_bookings": False,
        },
    )
    assert r.status_code == 200

    now_utc = datetime.now(timezone.utc)
    today_start = _day_start_utc(now_utc)

    # Customers for inactivity logic
    r = client.post("/crm/customers", headers=auth_headers, json={"name": "Active", "phone": "111"})
    assert r.status_code == 200
    active_customer_id = r.json()["id"]

    r = client.post("/crm/customers", headers=auth_headers, json={"name": "InactiveOld", "phone": "222"})
    assert r.status_code == 200
    inactive_old_customer_id = r.json()["id"]

    r = client.post("/crm/customers", headers=auth_headers, json={"name": "NeverVisited", "phone": "333"})
    assert r.status_code == 200

    # Completed appointment within last 60 days (keeps customer active)
    within_60 = today_start - timedelta(days=10) + timedelta(hours=12)
    r = client.post(
        "/crm/appointments",
        headers=auth_headers,
        json={
            "customer_id": active_customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": within_60.isoformat(),
            "ends_at": (within_60 + timedelta(minutes=60)).isoformat(),
            "status": "completed",
        },
    )
    assert r.status_code == 200

    # Completed appointment older than 60 days (marks customer inactive)
    older_60 = today_start - timedelta(days=90) + timedelta(hours=12)
    r = client.post(
        "/crm/appointments",
        headers=auth_headers,
        json={
            "customer_id": inactive_old_customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": older_60.isoformat(),
            "ends_at": (older_60 + timedelta(minutes=60)).isoformat(),
            "status": "completed",
        },
    )
    assert r.status_code == 200

    # An internal appointment today (counts as "appointments today")
    today_mid = today_start + timedelta(hours=12)
    r = client.post(
        "/crm/appointments",
        headers=auth_headers,
        json={
            "customer_id": active_customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": today_mid.isoformat(),
            "ends_at": (today_mid + timedelta(minutes=60)).isoformat(),
            "status": "booked",
        },
    )
    assert r.status_code == 200

    # Two online bookings created today (proxy: created_by_user_id is NULL)
    booking_a = today_start + timedelta(days=1, hours=10)
    r = client.post(
        f"/public/book/{slug}/appointments",
        json={
            "service_id": service_id,
            "starts_at": booking_a.isoformat(),
            "customer_name": "Booker A",
            "customer_phone": "9991",
        },
    )
    assert r.status_code == 200
    appointment_a_id = r.json()["appointment_id"]
    assert r.json()["needs_confirmation"] is True

    booking_b = today_start + timedelta(days=1, hours=11)
    r = client.post(
        f"/public/book/{slug}/appointments",
        json={
            "service_id": service_id,
            "starts_at": booking_b.isoformat(),
            "customer_name": "Booker B",
            "customer_phone": "9992",
        },
    )
    assert r.status_code == 200
    appointment_b_id = r.json()["appointment_id"]

    # Mark one of them completed to ensure "pending confirmation" excludes finalized statuses
    r = client.patch(
        f"/crm/appointments/{appointment_b_id}",
        headers=auth_headers,
        json={"status": "completed"},
    )
    assert r.status_code == 200

    r = client.get("/crm/dashboard/overview", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()

    assert body["timezone"] == "UTC"

    # Cards
    assert body["counts"]["appointments_today_count"] == 1
    assert body["counts"]["appointments_pending_confirmation_count"] == 1
    assert body["counts"]["inactive_customers_count"] >= 2  # InactiveOld + NeverVisited
    assert body["counts"]["new_online_bookings_count"] == 2

    # Lists (bounded)
    assert any(item["id"] == appointment_a_id for item in body["sections"]["appointments_pending_confirmation"])
    assert all(item["id"] != appointment_b_id for item in body["sections"]["appointments_pending_confirmation"])

