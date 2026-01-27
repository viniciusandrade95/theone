import os
import uuid

from fastapi.testclient import TestClient

from app.http.main import create_app

TENANT = str(uuid.uuid4())
os.environ.setdefault("ENV", "test")
os.environ.setdefault("APP_NAME", "beauty-crm")
os.environ.setdefault("DATABASE_URL", "dev")
os.environ.setdefault("SECRET_KEY", "dev")
os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")


def test_smoke_register_login_and_create_customer_and_analytics():
    app = create_app()
    client = TestClient(app)

    # Register
    r = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": TENANT},
        json={"email": "a@b.com", "password": "secret123"},
    )
    assert r.status_code == 200
    token = r.json()["token"]

    # Create customer
    r = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": TENANT, "Authorization": f"Bearer {token}"},
        json={"name": "Maria", "phone": "351111", "tags": ["VIP"]},
    )
    assert r.status_code == 200

    # Analytics (wide window)
    r = client.get(
        "/analytics/summary",
        headers={"X-Tenant-ID": TENANT, "Authorization": f"Bearer {token}"},
        params={"start": "2026-01-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "new_customers" in body
