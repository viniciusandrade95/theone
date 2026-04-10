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
    os.environ["CHATBOT_SERVICE_BASE_URL"] = "http://chatbot.local"
    os.environ["CHATBOT_SERVICE_TIMEOUT_SECONDS"] = "5"
    yield
    monkeypatch.setattr(loader, "_config", None)


def _register_and_login(client: TestClient, tenant_id: str):
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


def test_chatbot_message_and_reset(monkeypatch):
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())
    token = _register_and_login(client, tenant_id)

    calls = []

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload
            self.content = b"{}"

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(url, json, headers, timeout):
        calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        if url.endswith("/message"):
            return DummyResponse({"status": "ok", "reply": "hello from bot", "session_id": "s-123"})
        return DummyResponse({"status": "ok"})

    monkeypatch.setattr("modules.chatbot.service.chatbot_client.requests.post", fake_post)

    send = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}", "X-Trace-Id": "trace-123"},
        json={"message": "hi assistant", "surface": "dashboard"},
    )

    assert send.status_code == 200
    body = send.json()
    assert body["reply"]["text"] == "hello from bot"
    assert body["session_id"] == "s-123"
    assert body["client_id"] == tenant_id
    assert body["trace_id"] == "trace-123"

    reset = client.post(
        "/api/chatbot/reset",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"conversation_id": body["conversation_id"], "surface": "dashboard"},
    )
    assert reset.status_code == 200
    assert reset.json()["status"] == "reset"

    assert len(calls) == 2
    assert calls[0]["url"] == "http://chatbot.local/message"
    assert calls[1]["url"] == "http://chatbot.local/reset"
    assert calls[0]["json"]["client_id"] == tenant_id


def test_chatbot_requires_auth():
    app = create_app()
    client = TestClient(app)
    tenant_id = str(uuid.uuid4())

    resp = client.post(
        "/api/chatbot/message",
        headers={"X-Tenant-ID": tenant_id},
        json={"message": "hi"},
    )
    assert resp.status_code == 401
