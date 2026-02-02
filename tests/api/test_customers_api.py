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


def _register_and_login(client: TestClient, tenant_id: str):
    client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{tenant_id}@example.com", "password": "secret123"},
    )
    login = client.post(
        "/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{tenant_id}@example.com", "password": "secret123"},
    )
    return login.json()["token"]


def test_customer_crud_and_interactions():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    created = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Maria", "phone": "351111", "tags": ["VIP"]},
    )
    assert created.status_code == 200
    customer_id = created.json()["id"]

    listed = client.get(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"limit": 10, "offset": 0, "search": "maria"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    fetched = client.get(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Maria"

    updated = client.patch(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Maria Silva", "tags": ["VIP", "Lead"]},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Maria Silva"

    interaction = client.post(
        f"/crm/customers/{customer_id}/interactions",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"type": "note", "content": "Follow up soon"},
    )
    assert interaction.status_code == 200

    interactions = client.get(
        f"/crm/customers/{customer_id}/interactions",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert interactions.status_code == 200
    assert len(interactions.json()) == 1

    deleted = client.delete(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 200

    missing = client.get(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert missing.status_code == 404
