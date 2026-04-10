import uuid

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from requests import HTTPError, RequestException

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.errors import ValidationError
from modules.chatbot.repo.session_repo import ChatbotSessionRepo
from modules.chatbot.service.chatbot_client import ChatbotClient
from modules.chatbot.service.normalizer import normalize_chatbot_response

router = APIRouter()


class ChatbotMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: str | None = None
    session_id: str | None = None
    surface: str = Field(default="dashboard", max_length=64)
    customer_id: str | None = None


class ChatbotResetIn(BaseModel):
    conversation_id: str | None = None
    surface: str = Field(default="dashboard", max_length=64)


@router.post("/message")
def chatbot_message(
    payload: ChatbotMessageIn,
    identity=Depends(require_user),
    _tenant=Depends(require_tenant_header),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
):
    tenant_id = identity["tenant_id"]
    user_id = identity["user_id"]
    client_id = tenant_id

    effective_trace_id = x_trace_id or str(uuid.uuid4())

    with db_session() as session:
        repo = ChatbotSessionRepo(session)
        conversation = repo.get_or_create(
            tenant_id=tenant_id,
            user_id=user_id,
            client_id=client_id,
            surface=payload.surface,
            conversation_id=payload.conversation_id,
            customer_id=payload.customer_id,
        )

        upstream_payload = {
            "client_id": client_id,
            "conversation_id": str(conversation.conversation_id),
            "session_id": payload.session_id or conversation.chatbot_session_id,
            "message": payload.message,
            "surface": payload.surface,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "customer_id": payload.customer_id,
        }

        client = ChatbotClient()
        try:
            raw = client.send_message(payload=upstream_payload, trace_id=effective_trace_id)
        except HTTPError as err:
            status = err.response.status_code if err.response is not None else 502
            body = err.response.text if err.response is not None else str(err)
            repo.mark_message(entity=conversation, chatbot_session_id=payload.session_id, status="error", error=body)
            raise ValidationError("Chatbot service request failed", meta={"status": status})
        except RequestException as err:
            repo.mark_message(entity=conversation, chatbot_session_id=payload.session_id, status="error", error=str(err))
            raise ValidationError("Chatbot service unavailable")

        chatbot_session_id = raw.get("session_id") if isinstance(raw.get("session_id"), str) else (payload.session_id or conversation.chatbot_session_id)
        repo.mark_message(entity=conversation, chatbot_session_id=chatbot_session_id, status="active")

        normalized = normalize_chatbot_response(
            raw,
            conversation_id=str(conversation.conversation_id),
            chatbot_session_id=chatbot_session_id,
        )
        normalized["trace_id"] = effective_trace_id
        normalized["client_id"] = client_id
        return normalized


@router.post("/reset")
def chatbot_reset(
    payload: ChatbotResetIn,
    identity=Depends(require_user),
    _tenant=Depends(require_tenant_header),
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
):
    tenant_id = identity["tenant_id"]
    user_id = identity["user_id"]
    client_id = tenant_id

    effective_trace_id = x_trace_id or str(uuid.uuid4())

    with db_session() as session:
        repo = ChatbotSessionRepo(session)
        conversation = repo.get_or_create(
            tenant_id=tenant_id,
            user_id=user_id,
            client_id=client_id,
            surface=payload.surface,
            conversation_id=payload.conversation_id,
        )

        client = ChatbotClient()
        try:
            raw = client.reset(
                payload={
                    "client_id": client_id,
                    "conversation_id": str(conversation.conversation_id),
                    "session_id": conversation.chatbot_session_id,
                    "surface": payload.surface,
                    "user_id": user_id,
                },
                trace_id=effective_trace_id,
            )
        except RequestException:
            raw = {"status": "ok"}

        repo.reset(entity=conversation)

        return {
            "ok": True,
            "conversation_id": str(conversation.conversation_id),
            "session_id": None,
            "status": "reset",
            "trace_id": effective_trace_id,
            "meta": {"source": "chatbot1", "raw": raw},
        }
