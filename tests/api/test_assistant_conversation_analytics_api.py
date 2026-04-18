import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.http.main import create_app


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader
    from core.observability.metrics import reset_metrics
    from core.tenancy import clear_tenant_id

    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    clear_tenant_id()

    os.environ["ENV"] = "test"
    os.environ["APP_NAME"] = "beauty-crm"
    os.environ["DATABASE_URL"] = "dev"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["TENANT_HEADER"] = "X-Tenant-ID"
    os.environ["ASSISTANT_CONNECTOR_TOKEN"] = "test-connector-token"

    os.environ["CHATBOT_SERVICE_BASE_URL"] = "http://chatbot.local"
    os.environ["CHATBOT_SERVICE_TIMEOUT_SECONDS"] = "5"

    os.environ["WHATSAPP_WEBHOOK_SECRET"] = "whsec-test"
    os.environ["WHATSAPP_WEBHOOK_VERIFY_TOKEN"] = "verify-test"
    os.environ["WHATSAPP_CLOUD_ACCESS_TOKEN"] = "test-wa-token"
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"

    yield
    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    clear_tenant_id()


def _now_range() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(minutes=10)).isoformat()
    end = (now + timedelta(minutes=10)).isoformat()
    return start, end


def _sign(payload: dict, secret: str) -> str:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    import hmac
    import hashlib

    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def _register_and_login(client: TestClient, tenant_id: str) -> str:
    client.post(
        "/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{tenant_id}@example.com", "password": "secret123"},
    )
    login = client.post(
        "/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": f"{tenant_id}@example.com", "password": "secret123"},
    )
    assert login.status_code == 200
    return login.json()["token"]


def test_conversation_list_and_details_dashboard_and_whatsapp(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    # Enable WhatsApp feature + account for this tenant.
    from core.tenancy import clear_tenant_id, set_tenant_id
    from modules.billing.models import PlanTier
    from modules.messaging.models import WhatsAppAccount

    set_tenant_id(tenant_id)
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

    # Dashboard assistant upstream.
    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload
            self.content = b"{}"

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(url, json, headers, timeout):
        surface = (json or {}).get("surface")
        if surface == "whatsapp":
            return DummyResponse({"status": "ok", "reply": "Olá! Como posso ajudar?", "session_id": "wa-sess-1"})
        return DummyResponse({"status": "ok", "reply": "ok", "session_id": "dash-sess-1", "intent": "faq"})

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    # WhatsApp provider send.
    from modules.messaging.providers.meta_whatsapp_cloud import MetaWhatsAppCloudProvider
    from modules.messaging.providers.outbound_provider import OutboundSendResult

    def fake_send_whatsapp_text(self, **kwargs):
        return OutboundSendResult(provider="meta", provider_message_id="out-1")

    monkeypatch.setattr(MetaWhatsAppCloudProvider, "send_whatsapp_text", fake_send_whatsapp_text)

    # 1) Dashboard message
    dash = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Olá dashboard", "surface": "dashboard"},
    )
    assert dash.status_code == 200
    dash_conv = dash.json()["conversation_id"]

    # 2) WhatsApp inbound
    payload = {
        "provider": "meta",
        "external_event_id": "evt-1",
        "phone_number_id": "pn-123",
        "message_id": "m-1",
        "from_phone": "351911111111",
        "text": "Olá",
    }
    signature = _sign(payload, "whsec-test")
    wa = client.post("/messaging/inbound", json=payload, headers={"X-Hub-Signature-256": signature})
    assert wa.status_code == 200

    # Discover the WhatsApp conversation id (from persisted conversation).
    wa_convo = app.state.container.messaging_repo.get_conversation(tenant_id=tenant_id, customer_id=str(customer.id), channel="whatsapp")
    assert wa_convo is not None

    start, end = _now_range()
    listing = client.get(
        "/analytics/assistant/conversations",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"from": start, "to": end, "page": 1, "page_size": 50},
    )
    assert listing.status_code == 200
    items = listing.json()["items"]
    ids = {i["conversation_id"]: i for i in items}
    assert dash_conv in ids
    assert wa_convo.id in ids
    assert ids[dash_conv]["surface"] == "dashboard"
    assert ids[wa_convo.id]["surface"] == "whatsapp"

    dash_details = client.get(
        f"/analytics/assistant/conversations/{dash_conv}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert dash_details.status_code == 200
    turns = dash_details.json()["turns"]
    assert any(t.get("role") == "user" and "Olá dashboard" in (t.get("content") or "") for t in turns)

    wa_details = client.get(
        f"/analytics/assistant/conversations/{wa_convo.id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert wa_details.status_code == 200
    turns = wa_details.json()["turns"]
    assert any(t.get("role") == "user" and "Olá" in (t.get("content") or "") for t in turns)
    assert any(t.get("role") == "assistant" and "Como posso ajudar" in (t.get("content") or "") for t in turns)


def test_prebook_missing_phone_records_blocked_event_and_outcome(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    # Seed minimal CRM entities required for prebook.
    service = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Corte", "price_cents": 1000, "duration_minutes": 30, "is_active": True, "is_bookable_online": True},
    )
    assert service.status_code == 200
    service_id = service.json()["id"]
    loc = client.get("/crm/locations/default", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert loc.status_code == 200

    conv_id = str(uuid.uuid4())
    future_date = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()

    pb = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token"},
        json={
            "conversation_id": conv_id,
            "session_id": "s-guardrail",
            "customer": {"name": "Alice"},
            "booking": {"service_id": service_id, "requested_date": future_date, "requested_time": "12:00", "timezone": "Europe/Lisbon"},
        },
    )
    assert pb.status_code == 400
    assert "customer.phone is required" in pb.json()["message"]

    start, end = _now_range()
    listing = client.get(
        "/analytics/assistant/conversations",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        params={"from": start, "to": end, "page": 1, "page_size": 50},
    )
    assert listing.status_code == 200
    assert any(i["conversation_id"] == conv_id and i["outcome"] == "blocked_missing_data" for i in listing.json()["items"])

    details = client.get(
        f"/analytics/assistant/conversations/{conv_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert details.status_code == 200
    assert details.json()["outcome"] == "blocked_missing_data"
    assert details.json()["signals"]["missing_customer_phone"] >= 1
