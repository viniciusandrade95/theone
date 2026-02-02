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


def test_tenant_header_mismatch_is_blocked():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    response = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_a},
        json={"email": "a@b.com", "password": "secret123"},
    )
    assert response.status_code == 200
    token = response.json()["token"]

    response = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token}"},
        json={"name": "Maria", "phone": "351111"},
    )
    assert response.status_code == 401


def test_tenant_cannot_read_other_tenant_customer():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    response = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_a},
        json={"email": "a@b.com", "password": "secret123"},
    )
    assert response.status_code == 200
    token_a = response.json()["token"]

    response = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_b},
        json={"email": "b@c.com", "password": "secret123"},
    )
    assert response.status_code == 200
    token_b = response.json()["token"]

    create = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"name": "Maria", "phone": "351111"},
    )
    assert create.status_code == 200
    customer_id = create.json()["id"]

    forbidden = client.get(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
    )
    assert forbidden.status_code == 404
