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


def _register(client: TestClient, tenant_id: str, email: str) -> str:
    response = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "secret123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _get_settings(client: TestClient, tenant_id: str, token: str):
    return client.get(
        "/crm/settings",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )


def test_get_settings_auto_creates_row_and_links_default_location():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "settings-a@example.com")

    settings_response = _get_settings(client, tenant_id, token)
    assert settings_response.status_code == 200
    settings = settings_response.json()

    assert settings["tenant_id"] == tenant_id
    assert settings["calendar_default_view"] == "week"
    assert settings["default_timezone"] in {"UTC", "Etc/UTC", "GMT"}
    assert settings["default_location_id"] is not None

    default_location_response = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert default_location_response.status_code == 200
    assert default_location_response.json()["id"] == settings["default_location_id"]


def test_update_settings_and_tenant_isolation():
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "settings-b-a@example.com")
    token_b = _register(client, tenant_b, "settings-b-b@example.com")

    location_a = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
    )
    assert location_a.status_code == 200
    location_a_id = location_a.json()["id"]

    update_a = client.put(
        "/crm/settings",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={
            "business_name": "The One Beauty",
            "default_timezone": "America/Sao_Paulo",
            "currency": "brl",
            "calendar_default_view": "day",
            "default_location_id": location_a_id,
            "primary_color": "#0f172a",
            "logo_url": "https://cdn.example.com/logo.png",
        },
    )
    assert update_a.status_code == 200
    body_a = update_a.json()
    assert body_a["business_name"] == "The One Beauty"
    assert body_a["default_timezone"] == "America/Sao_Paulo"
    assert body_a["currency"] == "BRL"
    assert body_a["calendar_default_view"] == "day"
    assert body_a["default_location_id"] == location_a_id
    assert body_a["primary_color"] == "#0f172a"
    assert body_a["logo_url"] == "https://cdn.example.com/logo.png"

    settings_b = _get_settings(client, tenant_b, token_b)
    assert settings_b.status_code == 200
    body_b = settings_b.json()
    assert body_b["tenant_id"] == tenant_b
    assert body_b["business_name"] != "The One Beauty"
    assert body_b["default_location_id"] != location_a_id

    cross_tenant_assign = client.put(
        "/crm/settings",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={"default_location_id": location_a_id},
    )
    assert cross_tenant_assign.status_code == 400


def test_settings_location_helper_get_and_put():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "settings-location@example.com")

    get_location = client.get(
        "/crm/settings/location",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert get_location.status_code == 200
    location = get_location.json()
    assert location["id"]
    assert location["name"]
    assert location["timezone"]

    update_location = client.put(
        "/crm/settings/location",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Main Studio",
            "timezone": "America/New_York",
            "allow_overlaps": True,
            "hours_json": {"mon": {"open": "09:00", "close": "18:00"}},
        },
    )
    assert update_location.status_code == 200
    updated = update_location.json()
    assert updated["name"] == "Main Studio"
    assert updated["timezone"] == "America/New_York"
    assert updated["allow_overlaps"] is True
    assert updated["hours_json"] == {"mon": {"open": "09:00", "close": "18:00"}}

    deactivate_attempt = client.put(
        "/crm/settings/location",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert deactivate_attempt.status_code == 400
