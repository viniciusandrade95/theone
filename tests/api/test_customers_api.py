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
        json={
            "name": "Maria",
            "phone": "351111",
            "tags": ["VIP"],
            "stage": "lead",
            "consent_marketing": True,
            "consent_marketing_at": "2026-02-01T10:00:00Z",
        },
    )
    assert created.status_code == 200
    customer_id = created.json()["id"]
    assert created.json()["consent_marketing"] is True
    assert created.json()["consent_marketing_at"] == "2026-02-01T10:00:00+00:00"

    second = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Joana", "phone": "351222", "tags": ["retention"], "stage": "booked"},
    )
    assert second.status_code == 200

    listed = client.get(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"page": 1, "page_size": 10, "query": "maria"},
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["page"] == 1
    assert listed.json()["page_size"] == 10

    listed_stage = client.get(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"page": 1, "page_size": 10, "stage": "booked"},
    )
    assert listed_stage.status_code == 200
    assert listed_stage.json()["total"] == 1
    assert listed_stage.json()["items"][0]["name"] == "Joana"

    fetched = client.get(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Maria"

    updated = client.put(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Maria Silva", "tags": ["VIP", "Lead"], "stage": "completed"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Maria Silva"
    assert updated.json()["stage"] == "completed"

    interaction = client.post(
        f"/crm/customers/{customer_id}/interactions",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"type": "note", "content": "Follow up soon"},
    )
    assert interaction.status_code == 200
    assert interaction.json()["created_at"]

    interactions = client.get(
        f"/crm/customers/{customer_id}/interactions",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert interactions.status_code == 200
    assert interactions.json()["total"] == 1
    assert len(interactions.json()["items"]) == 1

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
