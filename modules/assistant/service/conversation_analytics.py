from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select

from modules.assistant.models.funnel_event_orm import AssistantFunnelEventORM
from modules.assistant.service.funnel_events import (
    ASSISTANT_CONVERSION_CONFIRMED,
    ASSISTANT_CUSTOMER_IDENTITY_MISSING,
    ASSISTANT_CUSTOMER_PHONE_MISSING,
    ASSISTANT_FALLBACK,
    ASSISTANT_HANDOFF_CREATED,
    ASSISTANT_MESSAGE_RECEIVED,
    ASSISTANT_MESSAGE_REPLIED,
    ASSISTANT_OPERATIONAL_FAILED,
    ASSISTANT_PREBOOK_CREATED,
    ASSISTANT_PREBOOK_FAILED,
)


# Minimal, operationally useful outcome taxonomy.
OUTCOME_COMPLETED_BOOKING = "completed_booking"
OUTCOME_COMPLETED_PREBOOK = "completed_prebook"
OUTCOME_HANDOFF = "handoff"
OUTCOME_BLOCKED_MISSING_DATA = "blocked_missing_data"
OUTCOME_FAILED_OPERATIONAL = "failed_operational"
OUTCOME_FALLBACK_ONLY = "fallback_only"
OUTCOME_UNKNOWN = "unknown"


@dataclass(frozen=True)
class ConversationSignals:
    messages_received: int = 0
    messages_replied: int = 0
    fallback: int = 0
    handoff_created: int = 0
    prebook_created: int = 0
    conversion_confirmed: int = 0
    prebook_failed: int = 0
    missing_customer_identity: int = 0
    missing_customer_phone: int = 0
    operational_failed: int = 0


def derive_outcome(signals: ConversationSignals) -> str:
    # Highest-confidence terminal outcomes first.
    if signals.conversion_confirmed > 0:
        return OUTCOME_COMPLETED_BOOKING
    if signals.prebook_created > 0:
        return OUTCOME_COMPLETED_PREBOOK
    if signals.handoff_created > 0:
        return OUTCOME_HANDOFF

    # Negative/blocked outcomes.
    if (signals.missing_customer_identity + signals.missing_customer_phone) > 0:
        return OUTCOME_BLOCKED_MISSING_DATA
    if (signals.prebook_failed + signals.operational_failed) > 0:
        return OUTCOME_FAILED_OPERATIONAL

    # Pure fallback.
    if signals.fallback > 0:
        return OUTCOME_FALLBACK_ONLY

    return OUTCOME_UNKNOWN


def abandoned_candidate(*, last_activity_at: datetime | None, now: datetime | None = None, threshold_hours: int = 24) -> bool:
    if last_activity_at is None:
        return False
    if last_activity_at.tzinfo is None:
        last_activity_at = last_activity_at.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return last_activity_at < (now - timedelta(hours=int(threshold_hours)))


def conversation_rollup_stmt(*, tenant_uuid: uuid.UUID, start: datetime, end: datetime):
    """SQL statement that rolls up assistant funnel events by conversation_id.

    This intentionally uses the funnel/event store as the join point so multiple surfaces
    (dashboard proxy, WhatsApp, prebook callbacks) can be analyzed consistently.
    """
    ev = AssistantFunnelEventORM
    return (
        select(
            ev.conversation_id.label("conversation_id"),
            func.min(ev.created_at).label("started_at"),
            func.max(ev.created_at).label("last_activity_at"),
            func.max(ev.assistant_session_id).label("assistant_session_id"),
            func.max(ev.channel).label("channel"),
            func.sum(case((ev.event_name == ASSISTANT_MESSAGE_RECEIVED, 1), else_=0)).label("messages_received"),
            func.sum(case((ev.event_name == ASSISTANT_MESSAGE_REPLIED, 1), else_=0)).label("messages_replied"),
            func.sum(case((ev.event_name == ASSISTANT_FALLBACK, 1), else_=0)).label("fallback"),
            func.sum(case((ev.event_name == ASSISTANT_HANDOFF_CREATED, 1), else_=0)).label("handoff_created"),
            func.sum(case((ev.event_name == ASSISTANT_PREBOOK_CREATED, 1), else_=0)).label("prebook_created"),
            func.sum(case((ev.event_name == ASSISTANT_CONVERSION_CONFIRMED, 1), else_=0)).label("conversion_confirmed"),
            func.sum(case((ev.event_name == ASSISTANT_PREBOOK_FAILED, 1), else_=0)).label("prebook_failed"),
            func.sum(case((ev.event_name == ASSISTANT_CUSTOMER_IDENTITY_MISSING, 1), else_=0)).label("missing_customer_identity"),
            func.sum(case((ev.event_name == ASSISTANT_CUSTOMER_PHONE_MISSING, 1), else_=0)).label("missing_customer_phone"),
            func.sum(case((ev.event_name == ASSISTANT_OPERATIONAL_FAILED, 1), else_=0)).label("operational_failed"),
        )
        .where(ev.tenant_id == tenant_uuid)
        .where(ev.created_at >= start)
        .where(ev.created_at < end)
        .where(ev.conversation_id.is_not(None))
        .group_by(ev.conversation_id)
        .order_by(func.max(ev.created_at).desc())
    )


def signals_from_row(row) -> ConversationSignals:
    def _get(name: str):
        if hasattr(row, name):
            return getattr(row, name)
        mapping = getattr(row, "_mapping", None)
        if mapping is not None:
            return mapping.get(name)
        try:
            return row[name]  # type: ignore[index]
        except Exception:
            return None

    return ConversationSignals(
        messages_received=int(_get("messages_received") or 0),
        messages_replied=int(_get("messages_replied") or 0),
        fallback=int(_get("fallback") or 0),
        handoff_created=int(_get("handoff_created") or 0),
        prebook_created=int(_get("prebook_created") or 0),
        conversion_confirmed=int(_get("conversion_confirmed") or 0),
        prebook_failed=int(_get("prebook_failed") or 0),
        missing_customer_identity=int(_get("missing_customer_identity") or 0),
        missing_customer_phone=int(_get("missing_customer_phone") or 0),
        operational_failed=int(_get("operational_failed") or 0),
    )
