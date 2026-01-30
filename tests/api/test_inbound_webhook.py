import json
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.http.main import create_app
from core.config import load_config
from core.tenancy import clear_tenant_id, set_tenant_id
from modules.messaging.models import WhatsAppAccount


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader
    monkeypatch.setattr(loader, "_config", None)
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    os.environ.setdefault("WHATSAPP_WEBHOOK_SECRET", "whsec-test")
    os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
    yield
    monkeypatch.setattr(loader, "_config", None)
    clear_tenant_id()


def _sign(payload: dict, secret: str) -> str:
    body = json.dumps(payload).encode("utf-8")
    import hmac
    import hashlib

    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def _setup_app():
    load_config()
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    set_tenant_id(tenant_id)
    app.state.container.tenant_service.create_tenant(tenant_id, name="Tenant")

    account = WhatsAppAccount.create(
        account_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        provider="meta",
        phone_number_id="pn-123",
    )
    app.state.container.messaging_repo.create_whatsapp_account(account)

    customer = app.state.container.crm.create_customer(name="Bea", phone="351111")
    clear_tenant_id()
    return app, client, tenant_id, customer


def test_inbound_webhook_rejects_invalid_signature():
    app, client, tenant_id, customer = _setup_app()

    payload = {
        "provider": "meta",
        "external_event_id": "evt-1",
        "phone_number_id": "pn-123",
        "message_id": "m-1",
        "from_phone": "351111",
        "text": "Oi",
    }
    response = client.post("/messaging/inbound", json=payload, headers={"X-Hub-Signature-256": "sha256=bad"})
    assert response.status_code == 401


def test_inbound_webhook_deduplicates_events():
    app, client, tenant_id, customer = _setup_app()

    payload = {
        "provider": "meta",
        "external_event_id": "evt-1",
        "phone_number_id": "pn-123",
        "message_id": "m-1",
        "from_phone": "351111",
        "text": "Oi",
    }
    signature = _sign(payload, "whsec-test")

    response = client.post("/messaging/inbound", json=payload, headers={"X-Hub-Signature-256": signature})
    assert response.status_code == 200

    response = client.post("/messaging/inbound", json=payload, headers={"X-Hub-Signature-256": signature})
    assert response.status_code == 200

    repo = app.state.container.messaging_repo
    assert repo.count_webhook_events(tenant_id=tenant_id) == 1
    assert repo.count_messages(tenant_id=tenant_id) == 1


def test_inbound_webhook_ignores_tenant_header_spoofing():
    app, client, tenant_id, customer = _setup_app()

    payload = {
        "provider": "meta",
        "external_event_id": "evt-2",
        "phone_number_id": "pn-123",
        "message_id": "m-2",
        "from_phone": "351111",
        "text": "Oi",
    }
    signature = _sign(payload, "whsec-test")

    other_tenant = str(uuid.uuid4())
    response = client.post(
        "/messaging/inbound",
        json=payload,
        headers={"X-Hub-Signature-256": signature, "X-Tenant-ID": other_tenant},
    )
    assert response.status_code == 200

    repo = app.state.container.messaging_repo
    assert repo.count_messages(tenant_id=tenant_id) == 1
    assert repo.count_messages(tenant_id=other_tenant) == 0
