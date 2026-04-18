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
    os.environ.setdefault("ASSISTANT_CONNECTOR_TOKEN", "test-connector-token")
    yield
    monkeypatch.setattr(loader, "_config", None)


def _register(client: TestClient, tenant_id: str, email: str) -> str:
    register = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "secret123"},
    )
    assert register.status_code == 200
    return register.json()["token"]


def _create_customer(client: TestClient, tenant_id: str, token: str) -> str:
    response = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Audit User", "phone": "11999998888"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _create_service(client: TestClient, tenant_id: str, token: str) -> str:
    response = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Corte", "price_cents": 2500, "duration_minutes": 45, "is_bookable_online": True},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _default_location(client: TestClient, tenant_id: str, token: str) -> str:
    response = client.get(
        "/crm/locations/default",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def _create_appointment(
    client: TestClient,
    *,
    tenant_id: str,
    token: str,
    customer_id: str,
    location_id: str,
    service_id: str,
    starts_at: str,
    ends_at: str,
) -> str:
    response = client.post(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": starts_at,
            "ends_at": ends_at,
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _operation_body(tenant_id: str, operation: str, payload: dict) -> dict:
    return {
        "tenant_id": tenant_id,
        "client_id": tenant_id,
        "session_id": "reschedule-test-session",
        "trace_id": "reschedule-test-trace",
        "idempotency_key": f"test:{operation}",
        "workflow_name": "reschedule_appointment" if operation != "lookup_availability" else "lookup_availability",
        "operation": operation,
        "payload": payload,
    }


def _assistant_headers(tenant_id: str) -> dict[str, str]:
    return {
        "X-Tenant-ID": tenant_id,
        "X-Assistant-Token": "test-connector-token",
        "X-Trace-Id": "reschedule-test-trace",
        "Idempotency-Key": "test:reschedule",
    }


def _setup_calendar(client: TestClient):
    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, f"{tenant_id}@example.com")
    customer_id = _create_customer(client, tenant_id, token)
    service_id = _create_service(client, tenant_id, token)
    location_id = _default_location(client, tenant_id, token)
    return tenant_id, token, customer_id, service_id, location_id


def test_internal_reschedule_request_updates_existing_appointment() -> None:
    app = create_app()
    client = TestClient(app)
    tenant_id, token, customer_id, service_id, location_id = _setup_calendar(client)
    appointment_id = _create_appointment(
        client,
        tenant_id=tenant_id,
        token=token,
        customer_id=customer_id,
        location_id=location_id,
        service_id=service_id,
        starts_at="2099-05-04T10:00:00Z",
        ends_at="2099-05-04T10:45:00Z",
    )

    availability = client.post(
        "/internal/chatbot/workflows/availability-lookup",
        headers=_assistant_headers(tenant_id),
        json=_operation_body(
            tenant_id,
            "lookup_availability",
            {"appointment_id": appointment_id, "new_date": "2099-05-04", "new_time": "16:00"},
        ),
    )
    assert availability.status_code == 200
    assert availability.json()["ok"] is True
    assert availability.json()["windows"][0]["label"] == "16:00"

    response = client.post(
        "/internal/chatbot/workflows/reschedule-request",
        headers=_assistant_headers(tenant_id),
        json=_operation_body(
            tenant_id,
            "reschedule_request",
            {"appointment_id": appointment_id, "new_date": "2099-05-04", "new_time": "16:00"},
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["operational_status"] == "ok"
    assert body["data"]["appointment_id"] == appointment_id

    listing = client.get(
        "/crm/appointments",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"from_dt": "2099-05-04T15:00:00Z", "to_dt": "2099-05-04T17:00:00Z"},
    )
    assert listing.status_code == 200
    updated = next(item for item in listing.json()["items"] if item["id"] == appointment_id)
    assert updated["starts_at"] == "2099-05-04T16:00:00"
    assert updated["ends_at"] == "2099-05-04T16:45:00"


def test_internal_reschedule_can_resolve_single_upcoming_appointment_without_reference() -> None:
    app = create_app()
    client = TestClient(app)
    tenant_id, token, customer_id, service_id, location_id = _setup_calendar(client)
    appointment_id = _create_appointment(
        client,
        tenant_id=tenant_id,
        token=token,
        customer_id=customer_id,
        location_id=location_id,
        service_id=service_id,
        starts_at="2099-05-04T11:00:00Z",
        ends_at="2099-05-04T11:45:00Z",
    )

    response = client.post(
        "/internal/chatbot/workflows/reschedule-request",
        headers=_assistant_headers(tenant_id),
        json=_operation_body(
            tenant_id,
            "reschedule_request",
            {"new_date": "2099-05-04", "new_time": "17:00"},
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["operational_status"] == "ok"
    assert body["data"]["appointment_id"] == appointment_id


def test_internal_reschedule_conflict_does_not_update_appointment() -> None:
    app = create_app()
    client = TestClient(app)
    tenant_id, token, customer_id, service_id, location_id = _setup_calendar(client)
    appointment_id = _create_appointment(
        client,
        tenant_id=tenant_id,
        token=token,
        customer_id=customer_id,
        location_id=location_id,
        service_id=service_id,
        starts_at="2099-05-05T10:00:00Z",
        ends_at="2099-05-05T10:45:00Z",
    )
    _create_appointment(
        client,
        tenant_id=tenant_id,
        token=token,
        customer_id=customer_id,
        location_id=location_id,
        service_id=service_id,
        starts_at="2099-05-05T16:00:00Z",
        ends_at="2099-05-05T16:45:00Z",
    )

    availability = client.post(
        "/internal/chatbot/workflows/availability-lookup",
        headers=_assistant_headers(tenant_id),
        json=_operation_body(
            tenant_id,
            "lookup_availability",
            {"appointment_id": appointment_id, "new_date": "2099-05-05", "new_time": "16:00"},
        ),
    )
    assert availability.status_code == 200
    availability_body = availability.json()
    assert availability_body["ok"] is True
    assert all(window["label"] != "16:00" for window in availability_body["windows"])

    response = client.post(
        "/internal/chatbot/workflows/reschedule-request",
        headers=_assistant_headers(tenant_id),
        json=_operation_body(
            tenant_id,
            "reschedule_request",
            {"appointment_id": appointment_id, "new_date": "2099-05-05", "new_time": "16:00"},
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["operational_status"] == "conflict"
    assert body["error_code"] == "appointment_overlap"


def test_internal_reschedule_requires_unambiguous_target() -> None:
    app = create_app()
    client = TestClient(app)
    tenant_id, token, customer_id, service_id, location_id = _setup_calendar(client)
    _create_appointment(
        client,
        tenant_id=tenant_id,
        token=token,
        customer_id=customer_id,
        location_id=location_id,
        service_id=service_id,
        starts_at="2099-05-06T10:00:00Z",
        ends_at="2099-05-06T10:45:00Z",
    )
    _create_appointment(
        client,
        tenant_id=tenant_id,
        token=token,
        customer_id=customer_id,
        location_id=location_id,
        service_id=service_id,
        starts_at="2099-05-06T12:00:00Z",
        ends_at="2099-05-06T12:45:00Z",
    )

    response = client.post(
        "/internal/chatbot/workflows/reschedule-request",
        headers=_assistant_headers(tenant_id),
        json=_operation_body(
            tenant_id,
            "reschedule_request",
            {"old_date": "2099-05-06", "new_date": "2099-05-07", "new_time": "16:00"},
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["operational_status"] == "validation_error"
    assert body["error_code"] == "appointment_ambiguous"
