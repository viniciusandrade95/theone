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


def _create_customer(client: TestClient, tenant_id: str, token: str, *, name: str, phone: str | None) -> str:
    payload = {"name": name}
    if phone is not None:
        payload["phone"] = phone
    r = client.post("/crm/customers", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}, json=payload)
    assert r.status_code == 200
    return r.json()["id"]


def _create_service(client: TestClient, tenant_id: str, token: str, *, name: str = "Service", duration_minutes: int = 30) -> str:
    r = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "price_cents": 1000, "duration_minutes": duration_minutes},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    r = client.get("/crm/locations/default", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    return r.json()["id"]


def _create_appointment(client: TestClient, tenant_id: str, token: str, *, customer_id: str, location_id: str, service_id: str) -> str:
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    ends_at = starts_at + timedelta(minutes=30)
    r = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "status": "booked",
        },
    )
    assert r.status_code == 200
    return r.json()["id"]


def test_preview_requires_context_for_appointment_variables():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "outbound-preview@example.com")
    customer_id = _create_customer(client, tenant_id, token, name="Alice", phone="351111111")

    tpl = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Reminder",
            "type": "reminder_24h",
            "channel": "whatsapp",
            "body": "Hi {{customer_name}}, see you at {{appointment_time}}",
            "is_active": True,
        },
    )
    assert tpl.status_code == 200

    preview = client.post(
        "/crm/outbound/preview",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"customer_id": customer_id, "template_id": tpl.json()["id"]},
    )
    assert preview.status_code == 400


def test_send_creates_history_and_interaction_on_success():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "outbound-send@example.com")
    customer_id = _create_customer(client, tenant_id, token, name="Bob", phone="351222222")

    tpl = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Campaign",
            "type": "simple_campaign",
            "channel": "whatsapp",
            "body": "Hello {{customer_name}}!",
            "is_active": True,
        },
    )
    assert tpl.status_code == 200
    template_id = tpl.json()["id"]

    preview = client.post(
        "/crm/outbound/preview",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"customer_id": customer_id, "template_id": template_id},
    )
    assert preview.status_code == 200

    send = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "template_id": template_id,
            "final_body": preview.json()["rendered_body"],
            "type": "simple_campaign",
            "channel": "whatsapp",
        },
    )
    assert send.status_code == 200
    body = send.json()
    assert body["ok"] is True
    assert body["outbound_message"]["status"] == "sent"
    assert body["whatsapp_url"]

    interactions = client.get(
        f"/crm/customers/{customer_id}/interactions",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"page": 1, "page_size": 50, "sort": "created_at", "order": "desc"},
    )
    assert interactions.status_code == 200
    types = [i["type"] for i in interactions.json()["items"]]
    assert "outbound_whatsapp" in types


def test_send_fails_without_phone_and_allows_resend_after_fix():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "outbound-nophone@example.com")
    customer_id = _create_customer(client, tenant_id, token, name="NoPhone", phone=None)

    tpl = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Reactivation",
            "type": "reactivation",
            "channel": "whatsapp",
            "body": "Hi {{customer_name}}",
            "is_active": True,
        },
    )
    assert tpl.status_code == 200
    template_id = tpl.json()["id"]

    send = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "template_id": template_id,
            "final_body": "Hi there",
            "type": "reactivation",
            "channel": "whatsapp",
        },
    )
    assert send.status_code == 200
    body = send.json()
    assert body["ok"] is False
    outbound_id = body["outbound_message"]["id"]
    assert body["outbound_message"]["status"] == "failed"

    # Fix phone and resend
    update = client.put(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"phone": "351333333"},
    )
    assert update.status_code == 200

    resend = client.post(
        f"/crm/outbound/{outbound_id}/resend",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert resend.status_code == 200
    assert resend.json()["ok"] is True

