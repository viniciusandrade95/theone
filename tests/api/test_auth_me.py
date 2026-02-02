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


def test_login_and_me_flow():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())

    response = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": "a@b.com", "password": "secret123"},
    )
    assert response.status_code == 200

    login = client.post(
        "/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": "a@b.com", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["token"]

    me = client.get(
        "/auth/me",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["tenant_id"] == tenant_id
    assert body["email"] == "a@b.com"
