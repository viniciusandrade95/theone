import os

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


def test_signup_creates_tenant_and_returns_token():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/auth/signup",
        json={"tenant_name": "Acme", "email": "a@b.com", "password": "secret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"]
    assert body["token"]
    assert body["user_id"]
