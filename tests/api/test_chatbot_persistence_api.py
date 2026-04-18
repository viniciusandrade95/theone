import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.http.main import create_app
from core.db.session import db_session
from core.observability.metrics import reset_metrics
from modules.chatbot.models.conversation_message_orm import ChatbotConversationMessageORM
from modules.chatbot.models.conversation_session_orm import ChatbotConversationSessionORM


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader

    monkeypatch.setattr(loader, "_config", None)
    reset_metrics()
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    os.environ["CHATBOT_SERVICE_BASE_URL"] = "http://chatbot.local"
    os.environ["CHATBOT_SERVICE_TIMEOUT_SECONDS"] = "5"
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


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_chatbot_persists_intent_state_and_history(monkeypatch):
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)
    customer_id = str(uuid.uuid4())

    def fake_post(url, json, headers, timeout):
        assert headers.get("X-Trace-Id")
        return DummyResponse(
            {
                "status": "ok",
                "reply": "hello from bot",
                "session_id": "s-123",
                "intent": "book_appointment",
                "handoff_requested": True,
                "handoff_reason": "user_requested_human",
                "slots": {"service": "haircut"},
                "context": {"timezone": "Europe/Lisbon"},
            }
        )

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    send = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "hi assistant", "surface": "dashboard", "customer_id": customer_id},
    )
    assert send.status_code == 200
    body = send.json()
    conversation_id = body["conversation_id"]

    with db_session() as session:
        conv = session.execute(
            select(ChatbotConversationSessionORM).where(ChatbotConversationSessionORM.conversation_id == uuid.UUID(conversation_id))
        ).scalar_one()
        assert str(conv.tenant_id) == tenant_id
        assert str(conv.customer_id) == customer_id
        assert conv.last_intent == "book_appointment"
        assert isinstance(conv.state_payload, dict)
        assert conv.state_payload.get("handoff", {}).get("requested") is True
        assert isinstance(conv.context_payload, dict)
        assert conv.context_payload.get("slots", {}).get("service") == "haircut"
        assert conv.conversation_epoch == 0

        msgs = session.execute(
            select(ChatbotConversationMessageORM)
            .where(ChatbotConversationMessageORM.conversation_id == uuid.UUID(conversation_id))
            .where(ChatbotConversationMessageORM.epoch == 0)
            .order_by(ChatbotConversationMessageORM.created_at.asc())
        ).scalars().all()
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[0].content == "hi assistant"
        assert msgs[1].role == "assistant"
        assert msgs[1].intent == "book_appointment"


def test_chatbot_reset_clears_state_and_increments_epoch(monkeypatch):
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    def fake_post(url, json, headers, timeout):
        if url.endswith("/message"):
            return DummyResponse({"status": "ok", "reply": "hello from bot", "session_id": "s-123", "intent": "book_appointment"})
        return DummyResponse({"status": "ok"})

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    send = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "hi", "surface": "dashboard"},
    )
    conversation_id = send.json()["conversation_id"]

    reset = client.post(
        "/api/chatbot/reset",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"conversation_id": conversation_id, "surface": "dashboard"},
    )
    assert reset.status_code == 200

    with db_session() as session:
        conv = session.execute(
            select(ChatbotConversationSessionORM).where(ChatbotConversationSessionORM.conversation_id == uuid.UUID(conversation_id))
        ).scalar_one()
        assert conv.conversation_epoch == 1
        assert conv.last_intent is None
        assert conv.state_payload is None

        msgs_epoch0 = session.execute(
            select(ChatbotConversationMessageORM)
            .where(ChatbotConversationMessageORM.conversation_id == uuid.UUID(conversation_id))
            .where(ChatbotConversationMessageORM.epoch == 0)
        ).scalars().all()
        assert len(msgs_epoch0) == 2

        msgs_epoch1 = session.execute(
            select(ChatbotConversationMessageORM)
            .where(ChatbotConversationMessageORM.conversation_id == uuid.UUID(conversation_id))
            .where(ChatbotConversationMessageORM.epoch == 1)
        ).scalars().all()
        assert any(m.role == "system" and m.content == "reset" for m in msgs_epoch1)


def test_chatbot_customer_id_persists_across_turns(monkeypatch):
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)
    customer_id = str(uuid.uuid4())

    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append(json)
        return DummyResponse({"status": "ok", "reply": "hello from bot", "session_id": "s-123"})

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    first = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "hi", "surface": "dashboard", "customer_id": customer_id},
    )
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "next", "surface": "dashboard", "conversation_id": conversation_id},
    )
    assert second.status_code == 200
    assert len(calls) == 2
    assert calls[0]["customer_id"] == customer_id
    assert calls[1]["customer_id"] == customer_id


def test_chatbot_start_new_resets_existing_scope_before_upstream_call(monkeypatch):
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    calls = []
    responses = [
        {"status": "ok", "reply": "old session", "session_id": "s-old", "intent": "book_appointment"},
        {"status": "ok", "reply": "fresh session", "session_id": "s-new", "intent": "book_appointment"},
    ]

    def fake_post(url, json, headers, timeout):
        calls.append(json)
        return DummyResponse(responses.pop(0))

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    first = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "old booking state", "surface": "dashboard"},
    )
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"message": "Quero marcar", "surface": "dashboard", "start_new": True},
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id
    assert calls[0]["session_id"] is None
    assert calls[1]["session_id"] is None

    with db_session() as session:
        conv = session.execute(
            select(ChatbotConversationSessionORM).where(ChatbotConversationSessionORM.conversation_id == uuid.UUID(conversation_id))
        ).scalar_one()
        assert conv.conversation_epoch == 1
        assert conv.chatbot_session_id == "s-new"


def test_chatbot_conversation_id_cannot_be_reused_cross_tenant(monkeypatch):
    app = create_app()
    client = TestClient(app)

    tenant_a = str(uuid.uuid4())
    token_a = _register_and_login(client, tenant_a)

    tenant_b = str(uuid.uuid4())
    token_b = _register_and_login(client, tenant_b)

    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append({"url": url, "json": json})
        return DummyResponse({"status": "ok", "reply": "hello from bot", "session_id": "s-123"})

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    first = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_a, "Authorization": f"Bearer {token_a}"},
        json={"message": "hi", "surface": "dashboard"},
    )
    conversation_id = first.json()["conversation_id"]
    assert len(calls) == 1

    # Attempt to reuse tenant A conversation_id under tenant B.
    resp = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_b, "Authorization": f"Bearer {token_b}"},
        json={"message": "hi", "surface": "dashboard", "conversation_id": conversation_id},
    )
    assert resp.status_code == 403
    assert len(calls) == 1  # no upstream call on rejected scope mismatch
