from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from core.observability.logging import log_event
from core.errors import ValidationError
from modules.assistant.contracts.slot_finding import AssistantSlotSuggestionsActionV1
from modules.assistant.service.handoff_service import AssistantHandoffService
from modules.assistant.service.slot_finding_service import SlotFindingService


BOOKING_INTENTS = {"find_slots", "check_availability", "book_appointment"}


@dataclass
class QuickwinResult:
    normalized: dict
    booking_state: dict | None = None
    booking_context: dict | None = None


def _safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def apply_assistant_quickwins(
    *,
    session,
    tenant_id: str,
    user_id: str | None,
    trace_id: str,
    conversation,
    normalized: dict,
    raw: dict,
) -> QuickwinResult:
    """Thin orchestration layer for assistant quick wins.

    - Uses upstream chatbot for intent/slot extraction (no NLP in `theone`).
    - Calls the existing booking availability source-of-truth for real slots.
    - Creates durable handoff records when requested.
    """

    # --------- handoff MVP
    if normalized.get("handoff", {}).get("requested"):
        service = AssistantHandoffService(session)
        reason = normalized.get("handoff", {}).get("reason") if isinstance(normalized.get("handoff"), dict) else None
        summary = "Pedido de atendente humano via assistant."
        if isinstance(raw.get("handoff_summary"), str) and raw["handoff_summary"].strip():
            summary = raw["handoff_summary"].strip()

        handoff, created = service.ensure_open_handoff(
            tenant_id=tenant_id,
            conversation_id=str(conversation.conversation_id),
            conversation_epoch=int(conversation.conversation_epoch or 0),
            surface=str(conversation.surface),
            session_id=str(conversation.chatbot_session_id) if conversation.chatbot_session_id else None,
            user_id=user_id,
            customer_id=str(conversation.customer_id) if conversation.customer_id else None,
            trace_id=trace_id,
            reason=reason,
            summary=summary,
        )
        actions = normalized.get("reply", {}).get("actions")
        if not isinstance(actions, list):
            actions = []
            normalized.setdefault("reply", {})["actions"] = actions
        actions.append(
            {
                "type": "assistant.handoff.v1",
                "handoff_id": str(handoff.id),
                "status": str(handoff.status),
                "created": bool(created),
            }
        )
        normalized.setdefault("meta", {}).setdefault("assistant", {})["handoff_id"] = str(handoff.id)
        normalized["reply"]["text"] = "Entendido — já pedi um atendente humano. A nossa equipa vai entrar em contacto em breve."

    # --------- slot finding quick win
    intent = normalized.get("intent")
    if not isinstance(intent, str) or intent not in BOOKING_INTENTS:
        return QuickwinResult(normalized=normalized)

    booking_slots = _safe_dict(raw.get("slots"))

    existing_state = getattr(conversation, "state_payload", None)
    booking_state: dict = dict(existing_state) if isinstance(existing_state, dict) else {}
    existing_ctx = getattr(conversation, "context_payload", None)
    booking_ctx: dict = dict(existing_ctx) if isinstance(existing_ctx, dict) else {}

    existing_booking = booking_state.get("booking")
    booking: dict = dict(existing_booking) if isinstance(existing_booking, dict) else {}
    # Merge in new extracted values from upstream.
    for key in ("service_id", "location_id", "requested_date"):
        if isinstance(booking_slots.get(key), str) and booking_slots.get(key):
            booking[key] = booking_slots[key]

    service_id = booking.get("service_id")
    location_id = booking.get("location_id")
    requested_date = booking.get("requested_date")

    missing: list[str] = []
    if not service_id:
        missing.append("service_id")
    if not requested_date:
        missing.append("date")

    actions = normalized.get("reply", {}).get("actions")
    if not isinstance(actions, list):
        actions = []
        normalized.setdefault("reply", {})["actions"] = actions

    if missing:
        # Persist what we already know, and ask deterministic follow-up.
        booking["missing"] = missing
        booking["updated_at"] = datetime.now(timezone.utc).isoformat()
        booking_state["booking"] = booking

        question = "Para que serviço?"
        if missing == ["date"]:
            question = "Para que dia?"
        elif len(missing) > 1:
            question = "Para que serviço e para que dia?"

        action = AssistantSlotSuggestionsActionV1(
            outcome="missing_info",
            trace_id=trace_id,
            missing=missing,
            message=question,
        )
        actions.append(action.model_dump(mode="json"))
        normalized["reply"]["text"] = question
        log_event("assistant_slot_finding_missing_info", tenant_id=tenant_id, trace_id=trace_id, missing=",".join(missing))
        return QuickwinResult(normalized=normalized, booking_state=booking_state, booking_context=booking_ctx)

    target_date = _parse_date(requested_date)
    if target_date is None:
        action = AssistantSlotSuggestionsActionV1(
            outcome="invalid",
            trace_id=trace_id,
            missing=[],
            message="Data inválida. Indica uma data no formato YYYY-MM-DD.",
        )
        actions.append(action.model_dump(mode="json"))
        normalized["reply"]["text"] = action.message or ""
        booking_state["booking"] = {**booking, "missing": ["date"]}
        return QuickwinResult(normalized=normalized, booking_state=booking_state, booking_context=booking_ctx)

    try:
        svc_id, loc_id, tz, slots = SlotFindingService(session).find_slots(
            tenant_id=tenant_id,
            service_id=str(service_id),
            target_date=target_date,
            location_id=str(location_id) if location_id else None,
            limit=5,
        )
    except ValidationError as e:
        action = AssistantSlotSuggestionsActionV1(
            outcome="invalid",
            trace_id=trace_id,
            missing=[],
            message=e.message,
        )
        actions.append(action.model_dump(mode="json"))
        normalized["reply"]["text"] = e.message
        return QuickwinResult(normalized=normalized, booking_state=booking_state, booking_context=booking_ctx)

    if not slots:
        action = AssistantSlotSuggestionsActionV1(
            outcome="no_slots",
            trace_id=trace_id,
            service_id=svc_id,
            location_id=loc_id,
            date=target_date.isoformat(),
            timezone=tz,
            slots=[],
            message="Não encontrei horários disponíveis para esse dia. Quer tentar outro dia?",
        )
        actions.append(action.model_dump(mode="json"))
        normalized["reply"]["text"] = action.message or ""
        booking["last_outcome"] = "no_slots"
        booking_state["booking"] = booking
        log_event("assistant_slot_finding_no_slots", tenant_id=tenant_id, trace_id=trace_id)
        return QuickwinResult(normalized=normalized, booking_state=booking_state, booking_context=booking_ctx)

    action = AssistantSlotSuggestionsActionV1(
        outcome="success",
        trace_id=trace_id,
        service_id=svc_id,
        location_id=loc_id,
        date=target_date.isoformat(),
        timezone=tz,
        slots=slots,
        message=None,
    )
    actions.append(action.model_dump(mode="json"))
    normalized["reply"]["text"] = "Tenho estes horários disponíveis: " + ", ".join([s.label for s in slots[:5]])

    booking["service_id"] = svc_id
    booking["location_id"] = loc_id
    booking["requested_date"] = target_date.isoformat()
    booking["missing"] = []
    booking["last_outcome"] = "success"
    booking["updated_at"] = datetime.now(timezone.utc).isoformat()
    booking_state["booking"] = booking
    booking_ctx["last_slot_suggestions"] = [s.model_dump(mode="json") for s in slots[:5]]

    log_event("assistant_slot_finding_success", tenant_id=tenant_id, trace_id=trace_id, slots_count=len(slots))
    return QuickwinResult(normalized=normalized, booking_state=booking_state, booking_context=booking_ctx)
