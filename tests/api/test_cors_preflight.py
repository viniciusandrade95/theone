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


def test_auth_me_preflight_allows_localhost_any_port():
    app = create_app()
    client = TestClient(app)

    response = client.options(
        "/auth/me",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-tenant-id",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3001"


def test_auth_me_preflight_allows_machine_hostname():
    app = create_app()
    client = TestClient(app)

    response = client.options(
        "/auth/me",
        headers={
            "Origin": "http://DESKTOP-NCKM9E7:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-tenant-id",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://DESKTOP-NCKM9E7:3000"


def test_auth_me_preflight_rejects_non_local_origin():
    app = create_app()
    client = TestClient(app)

    response = client.options(
        "/auth/me",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-tenant-id",
        },
    )

    assert response.status_code == 400
    assert "Disallowed CORS origin" in response.text


def test_auth_me_preflight_accepts_quoted_regex_env(monkeypatch):
    monkeypatch.setenv(
        "CORS_ALLOW_ORIGIN_REGEX",
        "'^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$'",
    )
    app = create_app()
    client = TestClient(app)

    response = client.options(
        "/auth/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-tenant-id",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
