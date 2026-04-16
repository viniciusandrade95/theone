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
    os.environ["ENV"] = "test"
    os.environ["APP_NAME"] = "beauty-crm"
    os.environ["DATABASE_URL"] = "dev"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["TENANT_HEADER"] = "X-Tenant-ID"
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "whsec-test"
    os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = "verify-token"
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
    yield
    monkeypatch.setattr(loader, "_config", None)
    clear_tenant_id()


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sign_bytes(body: bytes, secret: str) -> str:
    import hmac
    import hashlib

    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def _sign_json(payload: dict, secret: str) -> str:
    return _sign_bytes(_json_bytes(payload), secret)


def _setup_app():
    load_config()
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    set_tenant_id(tenant_id)
    app.state.container.tenant_service.create_tenant(tenant_id, name="Tenant")
    from modules.billing.models import PlanTier
    app.state.container.billing_service.set_plan(tier=PlanTier.PRO)

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
    signature = _sign_json(payload, "whsec-test")

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
    signature = _sign_json(payload, "whsec-test")

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


def test_meta_webhook_verification_get_returns_challenge():
    app, client, tenant_id, customer = _setup_app()
    r = client.get(
        "/messaging/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "verify-token", "hub.challenge": "abc123"},
    )
    assert r.status_code == 200
    assert r.text == "abc123"


def test_meta_webhook_verification_get_rejects_invalid_token():
    app, client, tenant_id, customer = _setup_app()
    r = client.get(
        "/messaging/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "abc123"},
    )
    assert r.status_code == 403


def _meta_inbound_payload(*, message_id: str) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "pn-123", "display_phone_number": "+351000000"},
                            "messages": [{"id": message_id, "from": "351111", "text": {"body": "Oi"}}],
                        }
                    }
                ]
            }
        ]
    }


def test_meta_webhook_post_ingests_inbound_message_meta_format():
    app, client, tenant_id, customer = _setup_app()

    payload = _meta_inbound_payload(message_id="wamid.inbound.1")
    raw = _json_bytes(payload)
    signature = _sign_bytes(raw, "whsec-test")

    r = client.post(
        "/messaging/webhook",
        data=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
    )
    assert r.status_code == 200
    assert r.json()["inbound_enqueued"] == 1

    repo = app.state.container.messaging_repo
    assert repo.count_webhook_events(tenant_id=tenant_id) == 1
    assert repo.count_messages(tenant_id=tenant_id) == 1


def test_meta_webhook_post_deduplicates_inbound_events():
    app, client, tenant_id, customer = _setup_app()

    payload = _meta_inbound_payload(message_id="wamid.inbound.2")
    raw = _json_bytes(payload)
    signature = _sign_bytes(raw, "whsec-test")

    r1 = client.post(
        "/messaging/webhook",
        data=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
    )
    assert r1.status_code == 200

    r2 = client.post(
        "/messaging/webhook",
        data=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
    )
    assert r2.status_code == 200

    repo = app.state.container.messaging_repo
    assert repo.count_webhook_events(tenant_id=tenant_id) == 1
    assert repo.count_messages(tenant_id=tenant_id) == 1
