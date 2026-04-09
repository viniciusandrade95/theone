import os
import uuid

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


def test_templates_crud_and_tenant_isolation():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "outbound-a@example.com")
    token_b = _register(client, tenant_b, "outbound-b@example.com")

    create = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={
            "name": "Confirm booking",
            "type": "booking_confirmation",
            "channel": "whatsapp",
            "body": "Hi {{customer_name}}",
            "is_active": True,
        },
    )
    assert create.status_code == 200
    template_id = create.json()["id"]

    list_a = client.get(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert list_a.status_code == 200
    assert list_a.json()["total"] == 1

    list_b = client.get(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
    )
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0

    patch = client.patch(
        f"/crm/outbound/templates/{template_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"is_active": False},
    )
    assert patch.status_code == 200
    assert patch.json()["is_active"] is False

    delete_other_tenant = client.delete(
        f"/crm/outbound/templates/{template_id}",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
    )
    assert delete_other_tenant.status_code == 404

    delete = client.delete(
        f"/crm/outbound/templates/{template_id}",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert delete.status_code == 200


def test_template_rejects_unknown_variables():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "outbound-unknown-vars@example.com")

    create = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Bad vars",
            "type": "simple_campaign",
            "channel": "whatsapp",
            "body": "Hello {{customer_name}} {{unknown}}",
            "is_active": True,
        },
    )
    assert create.status_code == 400

