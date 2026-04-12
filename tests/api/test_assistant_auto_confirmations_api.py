import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.http.main import create_app
from core.db.session import db_session
from modules.messaging.models.outbound_message_orm import OutboundMessageORM
from modules.messaging.models.whatsapp_account_orm import WhatsAppAccountORM


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader
    from core.observability.metrics import reset_metrics

    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    os.environ.setdefault("ASSISTANT_CONNECTOR_TOKEN", "test-connector-token")
    os.environ.setdefault("WHATSAPP_CLOUD_ACCESS_TOKEN", "test-wa-token")
    os.environ.setdefault("CHATBOT_SERVICE_BASE_URL", "http://chatbot.local")
    os.environ.setdefault("CHATBOT_SERVICE_TIMEOUT_SECONDS", "5")
    os.environ.setdefault("SMTP_HOST", "smtp.local")
    os.environ.setdefault("SMTP_FROM", "noreply@example.com")
    yield
    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()


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
    return login.json()["token"]


def _create_service(client: TestClient, *, tenant_id: str, token: str, name: str = "Haircut", duration_minutes: int = 30) -> str:
    resp = client.post(
        "/crm/services",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": name, "price_cents": 1000, "duration_minutes": duration_minutes, "is_active": True, "is_bookable_online": True},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _default_location(client: TestClient, *, tenant_id: str, token: str) -> str:
    resp = client.get("/crm/locations/default", headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    return resp.json()["id"]


def _create_customer(client: TestClient, *, tenant_id: str, token: str, name: str, phone: str, email: str | None = None) -> str:
    payload = {"name": name, "phone": phone}
    if email:
        payload["email"] = email
    resp = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _future_date() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()


def test_auto_confirmation_sent_on_prebook_created(monkeypatch):
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    service_id = _create_service(client, tenant_id=tenant_id, token=token)
    _ = _default_location(client, tenant_id=tenant_id, token=token)

    # Seed WhatsApp provider account for this tenant.
    with db_session() as session:
        session.add(
            WhatsAppAccountORM(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                provider="meta",
                phone_number_id="pn-123",
                status="active",
            )
        )
        session.flush()

    # Template used by automation.
    tpl = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Assistant Prebook Confirmation",
            "type": "assistant_prebook_confirmation",
            "channel": "whatsapp",
            "body": "Olá {{customer_name}}! Pré-reserva para {{service_name}} em {{appointment_date}} às {{appointment_time}}.",
            "is_active": True,
        },
    )
    assert tpl.status_code == 200

    from modules.messaging.providers.outbound_provider import OutboundSendResult

    def fake_send_whatsapp_text(self, *, phone_number_id, to_phone, body, trace_id, idempotency_key=None):
        return OutboundSendResult(provider="meta", provider_message_id="wamid.TEST.1")

    monkeypatch.setattr(
        "modules.messaging.providers.meta_whatsapp_cloud.MetaWhatsAppCloudProvider.send_whatsapp_text",
        fake_send_whatsapp_text,
    )

    payload = {
        "customer": {"name": "Maria", "phone": "+351900000000"},
        "booking": {
            "service_id": service_id,
            "requested_date": _future_date(),
            "requested_time": "12:00",
            "timezone": "Europe/Lisbon",
        },
    }
    resp = client.post(
        "/crm/assistant/prebook",
        headers={"X-Tenant-ID": tenant_id, "X-Assistant-Token": "test-connector-token", "Idempotency-Key": "wf:test:auto-confirm-1"},
        json=payload,
    )
    assert resp.status_code == 201
    appointment_id = resp.json()["data"]["appointment_id"]

    with db_session() as session:
        rows = (
            session.execute(
                select(OutboundMessageORM)
                .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id))
                .where(OutboundMessageORM.appointment_id == uuid.UUID(appointment_id))
                .where(OutboundMessageORM.trigger_type == "assistant_prebook_created")
            )
            .scalars()
            .all()
        )
        assert rows
        sent = [r for r in rows if r.status == "sent" and r.channel == "whatsapp"]
        assert sent
        assert sent[0].provider == "meta"
        assert sent[0].provider_message_id


def test_auto_confirmation_falls_back_to_email_when_whatsapp_unusable(monkeypatch):
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    _ = _default_location(client, tenant_id=tenant_id, token=token)
    customer_id = _create_customer(client, tenant_id=tenant_id, token=token, name="Bob", phone="123", email="bob@example.com")

    # Both templates exist, WhatsApp will fail due to invalid phone, then email should be used.
    tpl_wa = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Assistant Handoff Confirmation (WA)",
            "type": "assistant_handoff_confirmation",
            "channel": "whatsapp",
            "body": "Olá {{customer_name}}! Pedido de atendente recebido.",
            "is_active": True,
        },
    )
    assert tpl_wa.status_code == 200
    tpl_email = client.post(
        "/crm/outbound/templates",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={
            "name": "Assistant Handoff Confirmation (Email)",
            "type": "assistant_handoff_confirmation",
            "channel": "email",
            "body": "Olá {{customer_name}}! Pedido de atendente recebido.",
            "is_active": True,
        },
    )
    assert tpl_email.status_code == 200

    from modules.messaging.providers.outbound_provider import OutboundSendResult

    def fake_send_email_text(self, *, to_email, subject, body, trace_id, idempotency_key=None):
        return OutboundSendResult(provider="smtp", provider_message_id="email.TEST.1")

    monkeypatch.setattr(
        "modules.messaging.providers.smtp_email.SmtpEmailProvider.send_email_text",
        fake_send_email_text,
    )

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload
            self.content = b"{}"

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_chatbot_post(url, json, headers, timeout):
        return DummyResponse(
            {
                "status": "ok",
                "reply": "ok",
                "session_id": "s-123",
                "intent": "handoff",
                "handoff_requested": True,
                "handoff_reason": "user_requested_human",
            }
        )

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_chatbot_post)

    first = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Quero falar com um atendente", "surface": "dashboard", "customer_id": customer_id},
    )
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]

    with db_session() as session:
        rows = (
            session.execute(
                select(OutboundMessageORM)
                .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id))
                .where(OutboundMessageORM.customer_id == uuid.UUID(customer_id))
                .where(OutboundMessageORM.trigger_type == "assistant_handoff_created")
            )
            .scalars()
            .all()
        )
        assert rows
        sent_email = [r for r in rows if r.channel == "email" and r.status == "sent"]
        assert sent_email
        assert sent_email[0].recipient == "bob@example.com"

    # Should not send twice for the same active conversation epoch.
    again = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Preciso de um humano", "surface": "dashboard", "conversation_id": conversation_id},
    )
    assert again.status_code == 200

    with db_session() as session:
        rows2 = (
            session.execute(
                select(OutboundMessageORM)
                .where(OutboundMessageORM.tenant_id == uuid.UUID(tenant_id))
                .where(OutboundMessageORM.customer_id == uuid.UUID(customer_id))
                .where(OutboundMessageORM.trigger_type == "assistant_handoff_created")
            )
            .scalars()
            .all()
        )
        assert len(rows2) == len(rows)
