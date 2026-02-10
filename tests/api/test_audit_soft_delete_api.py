import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.http.main import create_app
from core.db.session import db_session
from modules.audit.models.audit_log_orm import AuditLogORM


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
    register = client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": email, "password": "secret123"},
    )
    assert register.status_code == 200
    return register.json()["token"]


def _headers(tenant_id: str, token: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}


def test_soft_delete_restore_and_audit_log():
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "audit-soft-delete@example.com")
    headers = _headers(tenant_id, token)

    customer = client.post(
        "/crm/customers",
        headers=headers,
        json={"name": "Maria Audit", "phone": "555100"},
    )
    assert customer.status_code == 200
    customer_id = customer.json()["id"]

    service = client.post(
        "/crm/services",
        headers=headers,
        json={"name": "Audit Service", "price_cents": 5000, "duration_minutes": 60},
    )
    assert service.status_code == 200
    service_id = service.json()["id"]

    default_location = client.get("/crm/locations/default", headers=headers)
    assert default_location.status_code == 200
    location_id = default_location.json()["id"]

    appointment = client.post(
        "/crm/appointments",
        headers=headers,
        json={
            "customer_id": customer_id,
            "location_id": location_id,
            "service_id": service_id,
            "starts_at": "2026-02-10T10:00:00Z",
            "ends_at": "2026-02-10T11:00:00Z",
        },
    )
    assert appointment.status_code == 200
    appointment_id = appointment.json()["id"]

    status_update = client.patch(
        f"/crm/appointments/{appointment_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "completed"

    delete_customer = client.delete(f"/crm/customers/{customer_id}", headers=headers)
    assert delete_customer.status_code == 200
    customers_after_delete = client.get("/crm/customers", headers=headers)
    assert customers_after_delete.status_code == 200
    assert customers_after_delete.json()["total"] == 0

    restore_customer = client.post(f"/crm/customers/{customer_id}/restore", headers=headers)
    assert restore_customer.status_code == 200
    customers_after_restore = client.get("/crm/customers", headers=headers)
    assert customers_after_restore.status_code == 200
    assert customers_after_restore.json()["total"] == 1

    delete_service = client.delete(f"/crm/services/{service_id}", headers=headers)
    assert delete_service.status_code == 200
    services_after_delete = client.get("/crm/services", headers=headers, params={"include_inactive": True})
    assert services_after_delete.status_code == 200
    assert all(item["id"] != service_id for item in services_after_delete.json()["items"])

    restore_service = client.post(f"/crm/services/{service_id}/restore", headers=headers)
    assert restore_service.status_code == 200
    services_after_restore = client.get("/crm/services", headers=headers, params={"include_inactive": True})
    assert services_after_restore.status_code == 200
    assert any(item["id"] == service_id for item in services_after_restore.json()["items"])

    delete_appointment = client.delete(f"/crm/appointments/{appointment_id}", headers=headers)
    assert delete_appointment.status_code == 200
    appts_after_delete = client.get(
        "/crm/appointments",
        headers=headers,
        params={
            "from_dt": "2026-02-01T00:00:00Z",
            "to_dt": "2026-03-01T00:00:00Z",
        },
    )
    assert appts_after_delete.status_code == 200
    assert appts_after_delete.json()["total"] == 0

    overview_after_delete = client.get(
        "/analytics/overview",
        headers=headers,
        params={"from": "2026-02-01T00:00:00Z", "to": "2026-03-01T00:00:00Z"},
    )
    assert overview_after_delete.status_code == 200
    assert overview_after_delete.json()["total_appointments_created"] == 0

    restore_appointment = client.post(f"/crm/appointments/{appointment_id}/restore", headers=headers)
    assert restore_appointment.status_code == 200
    appts_after_restore = client.get(
        "/crm/appointments",
        headers=headers,
        params={
            "from_dt": "2026-02-01T00:00:00Z",
            "to_dt": "2026-03-01T00:00:00Z",
        },
    )
    assert appts_after_restore.status_code == 200
    assert appts_after_restore.json()["total"] == 1

    with db_session() as session:
        rows = session.execute(
            select(AuditLogORM.entity_type, AuditLogORM.entity_id, AuditLogORM.action)
            .where(AuditLogORM.tenant_id == uuid.UUID(tenant_id))
            .order_by(AuditLogORM.created_at.asc())
        ).all()

    assert rows, "expected audit rows"
    actions = {(row.entity_type, str(row.entity_id), row.action) for row in rows}

    assert ("customer", customer_id, "created") in actions
    assert ("customer", customer_id, "deleted") in actions
    assert ("service", service_id, "created") in actions
    assert ("service", service_id, "deleted") in actions
    assert ("appointment", appointment_id, "created") in actions
    assert ("appointment", appointment_id, "status_changed") in actions
    assert ("appointment", appointment_id, "deleted") in actions
