import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.http.main import create_app


os.environ.setdefault("ENV", "test")
os.environ.setdefault("APP_NAME", "beauty-crm")
os.environ.setdefault("DATABASE_URL", "dev")
os.environ.setdefault("SECRET_KEY", "dev")
os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")


def _register(client: TestClient, tenant_id: str, email: str) -> str:
    r = client.post("/auth/register", headers={"X-Tenant-ID": tenant_id}, json={"email": email, "password": "secret123"})
    assert r.status_code == 200
    return r.json()["token"]


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    r = client.get("/crm/locations/default", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    return r.json()["id"]


def _update_default_location_hours(client: TestClient, tenant_id: str, token: str, *, timezone_name: str, hours_json: dict):
    r = client.put(
        "/crm/settings/location",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"timezone": timezone_name, "hours_json": hours_json},
    )
    assert r.status_code == 200


def _create_service(client: TestClient, tenant_id: str, token: str, *, name: str, duration: int = 30, price_cents: int = 1000) -> str:
    r = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "price_cents": price_cents, "duration_minutes": duration},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _set_service_bookable(client: TestClient, tenant_id: str, token: str, service_id: str, *, is_bookable: bool):
    r = client.patch(
        f"/crm/services/{service_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"is_bookable_online": is_bookable},
    )
    assert r.status_code == 200


def _enable_booking(client: TestClient, tenant_id: str, token: str, *, slug: str, business_name: str, min_notice: int = 0, max_days: int = 30, auto_confirm: bool = True):
    r = client.put(
        "/crm/booking/settings",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "booking_enabled": True,
            "booking_slug": slug,
            "public_business_name": business_name,
            "min_booking_notice_minutes": min_notice,
            "max_booking_notice_days": max_days,
            "auto_confirm_bookings": auto_confirm,
        },
    )
    assert r.status_code == 200


def _create_customer(client: TestClient, tenant_id: str, token: str, *, name: str, phone: str, email: str | None = None) -> str:
    payload = {"name": name, "phone": phone}
    if email:
        payload["email"] = email
    r = client.post("/crm/customers", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}, json=payload)
    assert r.status_code == 200
    return r.json()["id"]


def _count_customers(client: TestClient, tenant_id: str, token: str) -> int:
    r = client.get("/crm/customers", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    return int(r.json()["total"])


def test_public_booking_happy_path_and_reuse_customer():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "booking-happy@example.com")

    _default_location(client, tenant_id, token)
    _update_default_location_hours(client, tenant_id, token, timezone_name="America/New_York", hours_json={"mon": {"open": "09:00", "close": "18:00"}})

    service_id = _create_service(client, tenant_id, token, name="Haircut", duration=30)
    _set_service_bookable(client, tenant_id, token, service_id, is_bookable=True)
    _enable_booking(client, tenant_id, token, slug="my-studio", business_name="My Studio", min_notice=0, max_days=30, auto_confirm=True)

    # existing customer by phone
    _ = _create_customer(client, tenant_id, token, name="Alice", phone="351111")
    before = _count_customers(client, tenant_id, token)

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    availability = client.get(
        "/public/book/my-studio/availability",
        params={"service_id": service_id, "date": tomorrow},
    )
    assert availability.status_code == 200
    slots = availability.json()["slots"]
    assert len(slots) > 0
    starts_at = slots[0]["starts_at"]

    booking = client.post(
        "/public/book/my-studio/appointments",
        json={
            "service_id": service_id,
            "starts_at": starts_at,
            "customer_name": "Alice",
            "customer_phone": "351111",
            "customer_email": "alice@example.com",
            "note": "See you",
        },
    )
    assert booking.status_code == 200
    assert booking.json()["ok"] is True
    assert booking.json()["needs_confirmation"] is False

    after = _count_customers(client, tenant_id, token)
    assert after == before  # reused by phone, no duplicate


def test_public_booking_blocks_occupied_slot():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "booking-occupied@example.com")

    location_id = _default_location(client, tenant_id, token)
    service_id = _create_service(client, tenant_id, token, name="Massage", duration=60)
    _set_service_bookable(client, tenant_id, token, service_id, is_bookable=True)
    _enable_booking(client, tenant_id, token, slug="busy-studio", business_name="Busy Studio", min_notice=0, max_days=30, auto_confirm=False)

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    availability = client.get(
        "/public/book/busy-studio/availability",
        params={"service_id": service_id, "date": tomorrow, "location_id": location_id},
    )
    assert availability.status_code == 200
    slots = availability.json()["slots"]
    assert len(slots) > 0
    starts_at = slots[0]["starts_at"]
    ends_at = slots[0]["ends_at"]

    customer_id = _create_customer(client, tenant_id, token, name="Bob", phone="999")
    # occupy slot internally
    r = client.post(
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
    assert r.status_code == 200

    # should not be available anymore
    availability2 = client.get(
        "/public/book/busy-studio/availability",
        params={"service_id": service_id, "date": tomorrow, "location_id": location_id},
    )
    assert availability2.status_code == 200
    starts = {s["starts_at"] for s in availability2.json()["slots"]}
    assert starts_at not in starts

    booking = client.post(
        "/public/book/busy-studio/appointments",
        json={
            "service_id": service_id,
            "starts_at": starts_at,
            "location_id": location_id,
            "customer_name": "Charlie",
            "customer_phone": "777",
        },
    )
    assert booking.status_code == 409


def test_public_booking_respects_min_and_max_notice():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "booking-notice@example.com")

    location_id = _default_location(client, tenant_id, token)
    service_id = _create_service(client, tenant_id, token, name="Nails", duration=30)
    _set_service_bookable(client, tenant_id, token, service_id, is_bookable=True)
    _enable_booking(client, tenant_id, token, slug="notice-studio", business_name="Notice Studio", min_notice=60 * 24 * 10, max_days=1)

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    availability = client.get(
        "/public/book/notice-studio/availability",
        params={"service_id": service_id, "date": tomorrow, "location_id": location_id},
    )
    assert availability.status_code == 200
    assert availability.json()["slots"] == []


def test_public_booking_tenant_resolution_by_slug():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "booking-tenant-a@example.com")
    token_b = _register(client, tenant_b, "booking-tenant-b@example.com")

    _default_location(client, tenant_a, token_a)
    _default_location(client, tenant_b, token_b)

    svc_a = _create_service(client, tenant_a, token_a, name="Service A", duration=30)
    svc_b = _create_service(client, tenant_b, token_b, name="Service B", duration=30)
    _set_service_bookable(client, tenant_a, token_a, svc_a, is_bookable=True)
    _set_service_bookable(client, tenant_b, token_b, svc_b, is_bookable=True)

    _enable_booking(client, tenant_a, token_a, slug="tenant-a", business_name="Tenant A")
    _enable_booking(client, tenant_b, token_b, slug="tenant-b", business_name="Tenant B")

    cfg_a = client.get("/public/book/tenant-a")
    cfg_b = client.get("/public/book/tenant-b")
    assert cfg_a.status_code == 200
    assert cfg_b.status_code == 200
    assert cfg_a.json()["business_name"] == "Tenant A"
    assert cfg_b.json()["business_name"] == "Tenant B"


def test_public_booking_service_not_bookable_is_hidden_and_rejected():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "booking-nonbookable@example.com")

    location_id = _default_location(client, tenant_id, token)
    service_id = _create_service(client, tenant_id, token, name="Private Service", duration=30)
    _enable_booking(client, tenant_id, token, slug="private", business_name="Private")

    cfg = client.get("/public/book/private")
    assert cfg.status_code == 200
    assert cfg.json()["services"] == []

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    availability = client.get(
        "/public/book/private/availability",
        params={"service_id": service_id, "date": tomorrow, "location_id": location_id},
    )
    assert availability.status_code == 400

    booking = client.post(
        "/public/book/private/appointments",
        json={
            "service_id": service_id,
            "starts_at": (datetime.now(timezone.utc) + timedelta(days=1, hours=3)).isoformat(),
            "location_id": location_id,
            "customer_name": "Test",
            "customer_phone": "123",
        },
    )
    assert booking.status_code == 400


def test_public_booking_customer_phone_email_conflict_returns_error():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "booking-conflict@example.com")

    location_id = _default_location(client, tenant_id, token)
    service_id = _create_service(client, tenant_id, token, name="Hair", duration=30)
    _set_service_bookable(client, tenant_id, token, service_id, is_bookable=True)
    _enable_booking(client, tenant_id, token, slug="conflict", business_name="Conflict Studio", min_notice=0, max_days=30)

    _ = _create_customer(client, tenant_id, token, name="C1", phone="111", email="a@example.com")
    _ = _create_customer(client, tenant_id, token, name="C2", phone="222", email="b@example.com")

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    availability = client.get(
        "/public/book/conflict/availability",
        params={"service_id": service_id, "date": tomorrow, "location_id": location_id},
    )
    assert availability.status_code == 200
    starts_at = availability.json()["slots"][0]["starts_at"]

    booking = client.post(
        "/public/book/conflict/appointments",
        json={
            "service_id": service_id,
            "starts_at": starts_at,
            "location_id": location_id,
            "customer_name": "X",
            "customer_phone": "111",
            "customer_email": "b@example.com",
        },
    )
    assert booking.status_code == 400

