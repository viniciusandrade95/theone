from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from requests import HTTPError, RequestException

from app.http.deps import require_tenant_header, require_user
from core.observability.logging import log_event
from core.observability.metrics import start_timer
from core.observability.tracing import require_trace_id
from core.db.session import db_session
from core.errors import ValidationError
from modules.chatbot.repo.session_repo import ChatbotSessionRepo
from modules.chatbot.repo.message_history_repo import ChatbotMessageHistoryRepo
from modules.chatbot.service.chatbot_client import ChatbotClient
from modules.chatbot.service.normalizer import normalize_chatbot_response
from modules.assistant.service.assistant_quickwins import apply_assistant_quickwins

router = APIRouter()

_MAX_CONTEXT_BYTES = 8_000


def _clamp_json(value: object, *, max_bytes: int = _MAX_CONTEXT_BYTES) -> dict | None:
    if not isinstance(value, dict):
        return None
    # Avoid storing large/raw blobs. Best-effort clamp by serialized size.
    try:
        import json as _json

        raw = _json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if len(raw.encode("utf-8")) <= max_bytes:
            return value
    except Exception:
        return None
    return {"_truncated": True}


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

    effective_trace_id = require_trace_id()
    timer = start_timer()
    log_event("assistant_chatbot_request_started", surface="chatbot_message")

    with db_session() as session:
        repo = ChatbotSessionRepo(session)
        history = ChatbotMessageHistoryRepo(session)
        conversation = repo.get_or_create(
            tenant_id=tenant_id,
            user_id=user_id,
            client_id=client_id,
            surface=payload.surface,
            conversation_id=payload.conversation_id,
            customer_id=payload.customer_id,
        )

        # Persist the incoming user turn (compact).
        history.append(conversation=conversation, role="user", content=payload.message)

        upstream_payload = {
            "client_id": client_id,
            "conversation_id": str(conversation.conversation_id),
            "session_id": payload.session_id or conversation.chatbot_session_id,
            "message": payload.message,
            "surface": payload.surface,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "customer_id": payload.customer_id or (str(conversation.customer_id) if conversation.customer_id else None),
        }

        client = ChatbotClient()
        try:
            raw = client.send_message(payload=upstream_payload, trace_id=effective_trace_id)
        except HTTPError as err:
            status = err.response.status_code if err.response is not None else 502
            body = err.response.text if err.response is not None else str(err)
            repo.mark_message(entity=conversation, chatbot_session_id=payload.session_id, status="error", error=body)
            history.append(
                conversation=conversation,
                role="system",
                content="chatbot_upstream_failed",
                meta={"status": status},
            )
            log_event("assistant_chatbot_request_completed", level="error", surface="chatbot_message", status_code=status)
            raise ValidationError("Chatbot service request failed", meta={"status": status})
        except RequestException as err:
            repo.mark_message(entity=conversation, chatbot_session_id=payload.session_id, status="error", error=str(err))
            history.append(
                conversation=conversation,
                role="system",
                content="chatbot_upstream_failed",
                meta={"status": 502},
            )
            log_event("assistant_chatbot_request_completed", level="error", surface="chatbot_message", status_code=502)
            raise ValidationError("Chatbot service unavailable")

        chatbot_session_id = raw.get("session_id") if isinstance(raw.get("session_id"), str) else (payload.session_id or conversation.chatbot_session_id)
        repo.mark_message(entity=conversation, chatbot_session_id=chatbot_session_id, status="active")

        normalized = normalize_chatbot_response(
            raw,
            conversation_id=str(conversation.conversation_id),
            chatbot_session_id=chatbot_session_id,
        )

        # Apply thin assistant orchestration (slot suggestions / handoff MVP).
        quickwin = apply_assistant_quickwins(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
            trace_id=effective_trace_id,
            conversation=conversation,
            normalized=normalized,
            raw=raw,
        )
        normalized = quickwin.normalized

        normalized["trace_id"] = effective_trace_id
        normalized["client_id"] = client_id

        # Persist assistant continuity state (best-effort).
        intent_conf = raw.get("intent_confidence")
        confidence = float(intent_conf) if isinstance(intent_conf, (int, float)) else None

        state_payload = dict(conversation.state_payload) if isinstance(conversation.state_payload, dict) else {}
        context_payload = dict(conversation.context_payload) if isinstance(conversation.context_payload, dict) else {}

        if quickwin.booking_state:
            state_payload.update(quickwin.booking_state)
        if quickwin.booking_context:
            context_payload.update(quickwin.booking_context)

        if normalized.get("handoff", {}).get("requested"):
            state_payload["handoff"] = {
                "requested": True,
                "reason": normalized.get("handoff", {}).get("reason"),
                "at": datetime.now(tz=timezone.utc).isoformat(),
            }

        slots = _clamp_json(raw.get("slots"))
        if slots is not None:
            context_payload["slots"] = slots
        ctx = _clamp_json(raw.get("context"))
        if ctx is not None:
            context_payload["context"] = ctx

        repo.update_continuity(
            entity=conversation,
            last_intent=normalized.get("intent"),
            last_intent_confidence=confidence,
            state_payload=state_payload,
            context_payload=context_payload,
        )

        history.append(
            conversation=conversation,
            role="assistant",
            content=normalized.get("reply", {}).get("text") or "",
            intent=normalized.get("intent"),
            meta={
                "status": normalized.get("status"),
                "actions_count": len(normalized.get("reply", {}).get("actions") or []),
                "handoff_requested": bool(normalized.get("handoff", {}).get("requested")),
            },
        )
        log_event("assistant_chatbot_request_completed", surface="chatbot_message", status_code=200, duration_ms=int(timer.seconds() * 1000))
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

    effective_trace_id = require_trace_id()
    timer = start_timer()
    log_event("assistant_chatbot_request_started", surface="chatbot_reset")

    with db_session() as session:
        repo = ChatbotSessionRepo(session)
        history = ChatbotMessageHistoryRepo(session)
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
        history.append(conversation=conversation, role="system", content="reset", meta={"source": "api"})

        resp = {
            "ok": True,
            "conversation_id": str(conversation.conversation_id),
            "session_id": None,
            "status": "reset",
            "trace_id": effective_trace_id,
            "meta": {"source": "chatbot1", "raw": raw},
        }
        log_event("assistant_chatbot_request_completed", surface="chatbot_reset", status_code=200, duration_ms=int(timer.seconds() * 1000))
        return resp
