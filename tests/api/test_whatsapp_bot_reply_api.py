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
    os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = "verify-test"
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
    yield
    monkeypatch.setattr(loader, "_config", None)
    clear_tenant_id()


def _sign(payload: dict, secret: str) -> str:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    import hmac
    import hashlib

    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def _setup_app(*, monkeypatch):
    # Enable bot before loading config/app (reloading config in tests resets the in-memory DB).
    os.environ["CHATBOT_SERVICE_BASE_URL"] = "http://chatbot.local"
    os.environ["WHATSAPP_CLOUD_ACCESS_TOKEN"] = "test-wa-token"

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
        status="active",
    )
    app.state.container.messaging_repo.create_whatsapp_account(account)

    customer = app.state.container.crm.create_customer(name="Bea", phone="351911111111")

    clear_tenant_id()

    from modules.chatbot.service.chatbot_client import ChatbotClient
    from modules.messaging.providers.meta_whatsapp_cloud import MetaWhatsAppCloudProvider
    from modules.messaging.providers.outbound_provider import OutboundSendResult

    def fake_send_message(self, *, payload: dict, trace_id: str | None = None) -> dict:
        assert payload.get("surface") == "whatsapp"
        assert payload.get("conversation_id")
        assert payload.get("customer_id") == str(customer.id)
        return {"reply": "Olá! Como posso ajudar?", "session_id": "wa-sess-1"}

    monkeypatch.setattr(ChatbotClient, "send_message", fake_send_message)

    def fake_send_whatsapp_text(self, **kwargs):
        return OutboundSendResult(provider="meta", provider_message_id="out-1")

    monkeypatch.setattr(MetaWhatsAppCloudProvider, "send_whatsapp_text", fake_send_whatsapp_text)

    return app, client, tenant_id, customer


def test_whatsapp_webhook_verify_ok(monkeypatch):
    _, client, _, _ = _setup_app(monkeypatch=monkeypatch)
    resp = client.get(
        "/messaging/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "verify-test", "hub.challenge": "123"},
    )
    assert resp.status_code == 200
    assert resp.text == "123"


def test_inbound_triggers_bot_reply_and_persists_outbound(monkeypatch):
    app, client, tenant_id, customer = _setup_app(monkeypatch=monkeypatch)

    payload = {
        "provider": "meta",
        "external_event_id": "evt-1",
        "phone_number_id": "pn-123",
        "message_id": "m-1",
        "from_phone": "351911111111",
        "text": "Olá",
    }
    signature = _sign(payload, "whsec-test")

    response = client.post("/messaging/inbound", json=payload, headers={"X-Hub-Signature-256": signature})
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

    # Outbound message recorded (provider-backed).
    from core.db.session import db_session
    from modules.messaging.models.outbound_message_orm import OutboundMessageORM

    with db_session() as session:
        rows = session.query(OutboundMessageORM).filter(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id)).all()
        assert len(rows) == 1
        msg = rows[0]
        assert msg.type == "assistant_whatsapp_reply"
        assert msg.channel == "whatsapp"
        assert msg.status == "sent"
        assert msg.provider == "meta"
        assert msg.provider_message_id == "out-1"
        assert msg.delivery_status == "accepted"

    # Conversation continuity: assistant session id persisted.
    convo = app.state.container.messaging_repo.get_conversation(tenant_id=tenant_id, customer_id=str(customer.id), channel="whatsapp")
    assert convo is not None
    assert convo.assistant_session_id == "wa-sess-1"


def test_meta_webhook_entrypoint_enqueues_and_replies(monkeypatch):
    app, client, tenant_id, customer = _setup_app(monkeypatch=monkeypatch)

    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "phone_number_id": "pn-123",
                                "display_phone_number": "351000000000",
                            },
                            "messages": [
                                {
                                    "from": "351911111111",
                                    "id": "m-3",
                                    "timestamp": "1710000000",
                                    "type": "text",
                                    "text": {"body": "Olá"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
    signature = _sign(meta_payload, "whsec-test")

    response = client.post("/messaging/webhook", json=meta_payload, headers={"X-Hub-Signature-256": signature})
    assert response.status_code == 200
    assert response.json()["inbound_enqueued"] == 1

    from core.db.session import db_session
    from modules.messaging.models.outbound_message_orm import OutboundMessageORM

    with db_session() as session:
        rows = session.query(OutboundMessageORM).filter(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id)).all()
        assert len(rows) == 1


def test_inbound_dedup_does_not_send_twice(monkeypatch):
    app, client, tenant_id, customer = _setup_app(monkeypatch=monkeypatch)

    payload = {
        "provider": "meta",
        "external_event_id": "evt-1",
        "phone_number_id": "pn-123",
        "message_id": "m-1",
        "from_phone": "351911111111",
        "text": "Olá",
    }
    signature = _sign(payload, "whsec-test")

    response = client.post("/messaging/inbound", json=payload, headers={"X-Hub-Signature-256": signature})
    assert response.status_code == 200
    response = client.post("/messaging/inbound", json=payload, headers={"X-Hub-Signature-256": signature})
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

    from core.db.session import db_session
    from modules.messaging.models.outbound_message_orm import OutboundMessageORM

    with db_session() as session:
        rows = session.query(OutboundMessageORM).filter(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id)).all()
        assert len(rows) == 1
