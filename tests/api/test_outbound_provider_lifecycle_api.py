import hashlib
import hmac
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.http.main import create_app
from core.db.session import db_session
from core.observability.metrics import reset_metrics
from modules.messaging.models.outbound_delivery_event_orm import OutboundDeliveryEventORM
from modules.messaging.models.outbound_message_orm import OutboundMessageORM


os.environ.setdefault("ENV", "test")
os.environ.setdefault("APP_NAME", "beauty-crm")
os.environ.setdefault("DATABASE_URL", "dev")
os.environ.setdefault("SECRET_KEY", "dev")
os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader

    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    yield
    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()


def _register(client: TestClient, tenant_id: str, email: str) -> str:
    r = client.post("/auth/register", headers={"X-Tenant-ID": tenant_id}, json={"email": email, "password": "secret123"})
    assert r.status_code == 200
    return r.json()["token"]


def _create_customer(client: TestClient, tenant_id: str, token: str, *, name: str, phone: str) -> str:
    r = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "phone": phone},
    )
    assert r.status_code == 200
    return r.json()["id"]


def _create_template(client: TestClient, tenant_id: str, token: str) -> str:
    tpl = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Campaign",
            "type": "simple_campaign",
            "channel": "whatsapp",
            "body": "Hello {{customer_name}}!",
            "is_active": True,
        },
    )
    assert tpl.status_code == 200
    return tpl.json()["id"]


def _create_whatsapp_account(client: TestClient, tenant_id: str, token: str, *, phone_number_id: str):
    r = client.post(
        "/messaging/whatsapp-accounts",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"provider": "meta", "phone_number_id": phone_number_id, "status": "active"},
    )
    assert r.status_code == 200


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _json_bytes(payload: dict) -> bytes:
    import json as _json

    return _json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def test_outbound_provider_send_and_delivery_callback(monkeypatch):
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "wh-secret"
    os.environ["WHATSAPP_CLOUD_ACCESS_TOKEN"] = "token"
    os.environ["WHATSAPP_CLOUD_API_VERSION"] = "v19.0"
    os.environ["WHATSAPP_CLOUD_TIMEOUT_SECONDS"] = "3"

    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "provider-send@example.com")

    customer_id = _create_customer(client, tenant_id, token, name="Bob", phone="+351222222")
    template_id = _create_template(client, tenant_id, token)
    _create_whatsapp_account(client, tenant_id, token, phone_number_id="pn-123")

    def fake_post(url, json, headers, timeout):
        assert url.endswith("/pn-123/messages")
        assert headers.get("Authorization") == "Bearer token"
        return DummyResponse({"messages": [{"id": "wamid.123"}]})

    monkeypatch.setattr("modules.messaging.providers.meta_whatsapp_cloud.requests.post", fake_post)

    send = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}", "Idempotency-Key": "send:001"},
        json={"customer_id": customer_id, "template_id": template_id, "final_body": "Hello Bob!", "type": "simple_campaign", "channel": "whatsapp"},
    )
    assert send.status_code == 200
    body = send.json()
    assert body["ok"] is True
    assert body["whatsapp_url"] is None
    assert body["mode"] == "provider"
    assert body["requires_user_action"] is False
    outbound_id = body["outbound_message"]["id"]
    assert body["outbound_message"]["provider"] == "meta"
    assert body["outbound_message"]["provider_message_id"] == "wamid.123"
    assert body["outbound_message"]["delivery_status"] == "accepted"

    # Callback delivered
    payload = {
        "provider": "meta",
        "external_event_id": "evt-1",
        "phone_number_id": "pn-123",
        "provider_message_id": "wamid.123",
        "channel": "whatsapp",
        "status": "delivered",
        "payload": {"status": "delivered"},
    }
    import json as _json

    raw = _json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature = _sign("wh-secret", raw)
    cb = client.post("/messaging/delivery", data=raw, headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature})
    assert cb.status_code == 200
    assert cb.json()["recorded"] is True
    assert cb.json()["updated_message_id"] == outbound_id

    # Duplicate callback should dedupe by external_event_id.
    cb2 = client.post("/messaging/delivery", data=raw, headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature})
    assert cb2.status_code == 200
    assert cb2.json()["recorded"] is False

    with db_session() as session:
        msg = session.execute(
            select(OutboundMessageORM).where(OutboundMessageORM.id == uuid.UUID(outbound_id))
        ).scalar_one()
        assert msg.delivery_status in {"delivered", "read"}
        assert msg.delivered_at is not None

        events = session.execute(select(OutboundDeliveryEventORM)).scalars().all()
        assert len(events) == 1


def test_outbound_delivery_callback_via_meta_webhook_statuses(monkeypatch):
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "wh-secret"
    os.environ["WHATSAPP_CLOUD_ACCESS_TOKEN"] = "token"

    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "provider-meta-webhook@example.com")

    customer_id = _create_customer(client, tenant_id, token, name="Bob", phone="+351222222")
    template_id = _create_template(client, tenant_id, token)
    _create_whatsapp_account(client, tenant_id, token, phone_number_id="pn-123")

    def fake_post(url, json, headers, timeout):
        return DummyResponse({"messages": [{"id": "wamid.123"}]})

    monkeypatch.setattr("modules.messaging.providers.meta_whatsapp_cloud.requests.post", fake_post)

    send = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "template_id": template_id,
            "final_body": "Hello Bob!",
            "type": "simple_campaign",
            "channel": "whatsapp",
        },
    )
    assert send.status_code == 200
    assert send.json()["mode"] == "provider"
    outbound_id = send.json()["outbound_message"]["id"]

    meta_payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "pn-123"},
                            "statuses": [{"id": "wamid.123", "status": "delivered", "timestamp": "123"}],
                        }
                    }
                ]
            }
        ]
    }
    raw = _json_bytes(meta_payload)
    signature = _sign("wh-secret", raw)

    cb = client.post(
        "/messaging/webhook",
        data=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
    )
    assert cb.status_code == 200
    assert cb.json()["delivery_recorded"] == 1
    assert cb.json()["delivery_updated"] == 1

    cb2 = client.post(
        "/messaging/webhook",
        data=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
    )
    assert cb2.status_code == 200
    assert cb2.json()["delivery_recorded"] == 0

    with db_session() as session:
        msg = session.execute(select(OutboundMessageORM).where(OutboundMessageORM.id == uuid.UUID(outbound_id))).scalar_one()
        assert msg.delivery_status in {"delivered", "read"}
        assert msg.delivered_at is not None


def test_outbound_delivery_callback_is_tenant_safe(monkeypatch):
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "wh-secret"
    os.environ["WHATSAPP_CLOUD_ACCESS_TOKEN"] = "token"

    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    token_a = _register(client, tenant_a, "tenant-a@example.com")
    customer_a = _create_customer(client, tenant_a, token_a, name="Alice", phone="+351111111")
    tpl_a = _create_template(client, tenant_a, token_a)
    _create_whatsapp_account(client, tenant_a, token_a, phone_number_id="pn-a")

    tenant_b = str(uuid.uuid4())
    token_b = _register(client, tenant_b, "tenant-b@example.com")
    _create_whatsapp_account(client, tenant_b, token_b, phone_number_id="pn-b")

    def fake_post(url, json, headers, timeout):
        return DummyResponse({"messages": [{"id": "wamid.a"}]})

    monkeypatch.setattr("modules.messaging.providers.meta_whatsapp_cloud.requests.post", fake_post)

    send = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"customer_id": customer_a, "template_id": tpl_a, "final_body": "Hello", "type": "simple_campaign", "channel": "whatsapp"},
    )
    outbound_id = send.json()["outbound_message"]["id"]

    # Callback arrives routed to tenant B account, but references tenant A provider_message_id.
    payload = {
        "provider": "meta",
        "external_event_id": "evt-x",
        "phone_number_id": "pn-b",
        "provider_message_id": "wamid.a",
        "channel": "whatsapp",
        "status": "delivered",
        "payload": {"status": "delivered"},
    }
    import json as _json

    raw = _json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature = _sign("wh-secret", raw)
    cb = client.post("/messaging/delivery", data=raw, headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature})
    assert cb.status_code == 200
    assert cb.json()["updated_message_id"] is None

    with db_session() as session:
        msg = session.execute(select(OutboundMessageORM).where(OutboundMessageORM.id == uuid.UUID(outbound_id))).scalar_one()
        assert msg.delivery_status == "accepted"


def test_outbound_provider_send_failure_falls_back_to_deeplink(monkeypatch):
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "wh-secret"
    os.environ["WHATSAPP_CLOUD_ACCESS_TOKEN"] = "token"

    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "provider-fail@example.com")
    customer_id = _create_customer(client, tenant_id, token, name="Fail", phone="+351999999")
    template_id = _create_template(client, tenant_id, token)
    _create_whatsapp_account(client, tenant_id, token, phone_number_id="pn-999")

    def fake_post(url, json, headers, timeout):
        raise RuntimeError("boom")

    monkeypatch.setattr("modules.messaging.providers.meta_whatsapp_cloud.requests.post", fake_post)

    send = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer_id,
            "template_id": template_id,
            "final_body": "Hello",
            "type": "simple_campaign",
            "channel": "whatsapp",
        },
    )
    assert send.status_code == 200
    body = send.json()
    assert body["ok"] is False
    assert body["whatsapp_url"]  # fallback for manual send
    assert body["mode"] == "deeplink"
    assert body["requires_user_action"] is True
    assert body["outbound_message"]["status"] == "failed"
    assert body["outbound_message"]["error_code"] == "provider_send_failed"


def test_outbound_send_idempotency_key_replay_does_not_duplicate_provider_send(monkeypatch):
    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "wh-secret"
    os.environ["WHATSAPP_CLOUD_ACCESS_TOKEN"] = "token"
    os.environ["WHATSAPP_CLOUD_API_VERSION"] = "v19.0"

    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register(client, tenant_id, "provider-idempotency@example.com")

    customer_id = _create_customer(client, tenant_id, token, name="Bob", phone="+351222222")
    template_id = _create_template(client, tenant_id, token)
    _create_whatsapp_account(client, tenant_id, token, phone_number_id="pn-123")

    calls: list[str] = []

    def fake_post(url, json, headers, timeout):
        calls.append(url)
        return DummyResponse({"messages": [{"id": "wamid.123"}]})

    monkeypatch.setattr("modules.messaging.providers.meta_whatsapp_cloud.requests.post", fake_post)

    payload = {"customer_id": customer_id, "template_id": template_id, "final_body": "Hello Bob!", "type": "simple_campaign", "channel": "whatsapp"}

    send1 = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}", "Idempotency-Key": "send:replay:001"},
        json=payload,
    )
    assert send1.status_code == 200
    body1 = send1.json()
    assert body1["ok"] is True
    assert body1["mode"] == "provider"
    assert body1["idempotency_replay"] is False

    send2 = client.post(
        "/crm/outbound/send",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}", "Idempotency-Key": "send:replay:001"},
        json=payload,
    )
    assert send2.status_code == 200
    body2 = send2.json()
    assert body2["outbound_message"]["id"] == body1["outbound_message"]["id"]
    assert body2["idempotency_replay"] is True
    assert body2["mode"] == "provider"
    assert len(calls) == 1
