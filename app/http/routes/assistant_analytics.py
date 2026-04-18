import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, distinct, func, select

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.errors import ValidationError
from core.tenancy import require_tenant_id
from modules.assistant.models.funnel_event_orm import AssistantFunnelEventORM
from modules.assistant.service.conversation_analytics import (
    abandoned_candidate,
    conversation_rollup_stmt,
    ConversationSignals,
    derive_outcome,
    signals_from_row,
)
from modules.assistant.service.funnel_events import (
    ASSISTANT_CONVERSATION_RESET,
    ASSISTANT_CONVERSATION_STARTED,
    ASSISTANT_CONVERSION_CONFIRMED,
    ASSISTANT_CUSTOMER_IDENTITY_MISSING,
    ASSISTANT_CUSTOMER_PHONE_MISSING,
    ASSISTANT_FALLBACK,
    ASSISTANT_HANDOFF_CREATED,
    ASSISTANT_HANDOFF_REQUESTED,
    ASSISTANT_MESSAGE_RECEIVED,
    ASSISTANT_MESSAGE_REPLIED,
    ASSISTANT_PREBOOK_CREATED,
    ASSISTANT_PREBOOK_FAILED,
    ASSISTANT_PREBOOK_REQUESTED,
    ASSISTANT_OPERATIONAL_FAILED,
)
from modules.chatbot.models.conversation_message_orm import ChatbotConversationMessageORM
from modules.chatbot.models.conversation_session_orm import ChatbotConversationSessionORM
from modules.messaging.models.conversation_orm import ConversationORM
from modules.messaging.models.message_orm import MessageORM
from modules.messaging.models.outbound_message_orm import OutboundMessageORM


router = APIRouter()


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _validate_range(from_dt: datetime, to_dt: datetime) -> tuple[datetime, datetime]:
    start = _to_utc(from_dt)
    end = _to_utc(to_dt)
    if start >= end:
        raise ValidationError("invalid_range", meta={"from": start.isoformat(), "to": end.isoformat()})
    return start, end


@router.get("/assistant/overview")
def assistant_overview(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_uuid = uuid.UUID(require_tenant_id())
    start, end = _validate_range(from_dt, to_dt)

    with db_session() as session:
        filters = [
            AssistantFunnelEventORM.tenant_id == tenant_uuid,
            AssistantFunnelEventORM.created_at >= start,
            AssistantFunnelEventORM.created_at < end,
        ]
        stmt = select(
            func.count().label("total_events"),
            func.count(distinct(AssistantFunnelEventORM.conversation_id)).label("unique_conversations"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_MESSAGE_RECEIVED, 1), else_=0)).label("messages_received"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_MESSAGE_REPLIED, 1), else_=0)).label("messages_replied"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_FALLBACK, 1), else_=0)).label("fallback_count"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_HANDOFF_REQUESTED, 1), else_=0)).label("handoff_requested"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_HANDOFF_CREATED, 1), else_=0)).label("handoff_created"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_PREBOOK_REQUESTED, 1), else_=0)).label("prebook_requested"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_PREBOOK_CREATED, 1), else_=0)).label("prebook_created"),
            func.sum(case((AssistantFunnelEventORM.event_name == ASSISTANT_CONVERSION_CONFIRMED, 1), else_=0)).label("conversion_confirmed"),
        ).where(*filters)
        row = session.execute(stmt).one()

        # Outbound delivery-oriented stats (assistant-triggered only).
        outbound_stmt = (
            select(
                OutboundMessageORM.channel,
                OutboundMessageORM.status,
                func.count(OutboundMessageORM.id).label("count"),
            )
            .where(OutboundMessageORM.tenant_id == tenant_uuid)
            .where(OutboundMessageORM.trigger_type.in_(["assistant_prebook_created", "assistant_handoff_created"]))
            .where(OutboundMessageORM.created_at >= start)
            .where(OutboundMessageORM.created_at < end)
            .group_by(OutboundMessageORM.channel, OutboundMessageORM.status)
            .order_by(OutboundMessageORM.channel.asc(), OutboundMessageORM.status.asc())
        )
        outbound_rows = session.execute(outbound_stmt).all()

    outbound = [
        {"channel": (r.channel or ""), "status": (r.status or ""), "count": int(r.count or 0)} for r in outbound_rows
    ]

    prebook_created = int(row.prebook_created or 0)
    conversion_confirmed = int(row.conversion_confirmed or 0)
    conversion_rate = round((conversion_confirmed / prebook_created), 4) if prebook_created else 0.0

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "tenant_id": str(tenant_uuid),
        "messages": {"received": int(row.messages_received or 0), "replied": int(row.messages_replied or 0)},
        "unique_conversations": int(row.unique_conversations or 0),
        "fallback": int(row.fallback_count or 0),
        "handoff": {"requested": int(row.handoff_requested or 0), "created": int(row.handoff_created or 0)},
        "prebook": {"requested": int(row.prebook_requested or 0), "created": prebook_created},
        "conversion": {"confirmed": conversion_confirmed, "rate": conversion_rate},
        "outbound": outbound,
    }


@router.get("/assistant/funnel")
def assistant_funnel(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_uuid = uuid.UUID(require_tenant_id())
    start, end = _validate_range(from_dt, to_dt)
    stages = [
        ASSISTANT_MESSAGE_RECEIVED,
        ASSISTANT_MESSAGE_REPLIED,
        ASSISTANT_FALLBACK,
        ASSISTANT_HANDOFF_REQUESTED,
        ASSISTANT_HANDOFF_CREATED,
        ASSISTANT_PREBOOK_REQUESTED,
        ASSISTANT_PREBOOK_CREATED,
        ASSISTANT_CONVERSION_CONFIRMED,
    ]
    with db_session() as session:
        stmt = (
            select(AssistantFunnelEventORM.event_name, func.count(AssistantFunnelEventORM.id))
            .where(AssistantFunnelEventORM.tenant_id == tenant_uuid)
            .where(AssistantFunnelEventORM.created_at >= start)
            .where(AssistantFunnelEventORM.created_at < end)
            .where(AssistantFunnelEventORM.event_name.in_(stages))
            .group_by(AssistantFunnelEventORM.event_name)
        )
        rows = {name: int(count or 0) for name, count in session.execute(stmt).all()}
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "tenant_id": str(tenant_uuid),
        "stages": [{"event": name, "count": rows.get(name, 0)} for name in stages],
    }


@router.get("/assistant/channels")
def assistant_channels(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_uuid = uuid.UUID(require_tenant_id())
    start, end = _validate_range(from_dt, to_dt)
    with db_session() as session:
        stmt = (
            select(
                OutboundMessageORM.channel,
                OutboundMessageORM.provider,
                OutboundMessageORM.status,
                func.count(OutboundMessageORM.id).label("count"),
            )
            .where(OutboundMessageORM.tenant_id == tenant_uuid)
            .where(OutboundMessageORM.trigger_type.in_(["assistant_prebook_created", "assistant_handoff_created"]))
            .where(OutboundMessageORM.created_at >= start)
            .where(OutboundMessageORM.created_at < end)
            .group_by(OutboundMessageORM.channel, OutboundMessageORM.provider, OutboundMessageORM.status)
            .order_by(OutboundMessageORM.channel.asc(), OutboundMessageORM.provider.asc(), OutboundMessageORM.status.asc())
        )
        rows = session.execute(stmt).all()
    items = [
        {
            "channel": (r.channel or ""),
            "provider": (r.provider or ""),
            "status": (r.status or ""),
            "count": int(r.count or 0),
        }
        for r in rows
    ]
    return {"from": start.isoformat(), "to": end.isoformat(), "tenant_id": str(tenant_uuid), "items": items}


@router.get("/assistant/templates")
def assistant_templates(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_uuid = uuid.UUID(require_tenant_id())
    start, end = _validate_range(from_dt, to_dt)
    with db_session() as session:
        stmt = (
            select(
                OutboundMessageORM.type,
                OutboundMessageORM.channel,
                OutboundMessageORM.status,
                func.count(OutboundMessageORM.id).label("count"),
            )
            .where(OutboundMessageORM.tenant_id == tenant_uuid)
            .where(OutboundMessageORM.trigger_type.in_(["assistant_prebook_created", "assistant_handoff_created"]))
            .where(OutboundMessageORM.created_at >= start)
            .where(OutboundMessageORM.created_at < end)
            .group_by(OutboundMessageORM.type, OutboundMessageORM.channel, OutboundMessageORM.status)
            .order_by(OutboundMessageORM.type.asc(), OutboundMessageORM.channel.asc(), OutboundMessageORM.status.asc())
        )
        rows = session.execute(stmt).all()
    items = [
        {"type": (r.type or ""), "channel": (r.channel or ""), "status": (r.status or ""), "count": int(r.count or 0)}
        for r in rows
    ]
    return {"from": start.isoformat(), "to": end.isoformat(), "tenant_id": str(tenant_uuid), "items": items}


@router.get("/assistant/conversions")
def assistant_conversions(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_uuid = uuid.UUID(require_tenant_id())
    start, end = _validate_range(from_dt, to_dt)
    with db_session() as session:
        base = (
            select(AssistantFunnelEventORM.event_name, func.count(AssistantFunnelEventORM.id).label("count"))
            .where(AssistantFunnelEventORM.tenant_id == tenant_uuid)
            .where(AssistantFunnelEventORM.created_at >= start)
            .where(AssistantFunnelEventORM.created_at < end)
            .where(AssistantFunnelEventORM.event_name.in_([ASSISTANT_PREBOOK_CREATED, ASSISTANT_CONVERSION_CONFIRMED]))
            .group_by(AssistantFunnelEventORM.event_name)
        )
        rows = {name: int(count or 0) for name, count in session.execute(base).all()}
    prebook_created = rows.get(ASSISTANT_PREBOOK_CREATED, 0)
    conversion_confirmed = rows.get(ASSISTANT_CONVERSION_CONFIRMED, 0)
    rate = round((conversion_confirmed / prebook_created), 4) if prebook_created else 0.0
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "tenant_id": str(tenant_uuid),
        "prebook_created": prebook_created,
        "conversion_confirmed": conversion_confirmed,
        "conversion_rate": rate,
    }


@router.get("/assistant/conversations")
def assistant_conversations(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    surface: str | None = Query(default=None, description="Optional surface filter: dashboard|whatsapp"),
    outcome: str | None = Query(default=None, description="Optional derived outcome filter."),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    """List assistant conversations for analytics/debugging (tenant-scoped).

    Note: this endpoint returns *summaries* (no message bodies). Conversation text is available
    only via the details endpoint, and should be treated as sensitive data.
    """
    tenant_uuid = uuid.UUID(require_tenant_id())
    start, end = _validate_range(from_dt, to_dt)
    offset = (page - 1) * page_size

    with db_session() as session:
        base = conversation_rollup_stmt(tenant_uuid=tenant_uuid, start=start, end=end).subquery()
        total = int(session.execute(select(func.count()).select_from(base)).scalar_one() or 0)
        stmt = select(base).offset(offset).limit(page_size)
        rows = session.execute(stmt).all()

        conv_ids = [r.conversation_id for r in rows if r.conversation_id is not None]
        chatbot: dict[object, dict[str, object]] = {}
        whatsapp: dict[object, dict[str, object]] = {}
        if conv_ids:
            for r in (
                session.execute(
                    select(ChatbotConversationSessionORM).where(ChatbotConversationSessionORM.tenant_id == tenant_uuid).where(
                        ChatbotConversationSessionORM.conversation_id.in_(conv_ids)
                    )
                )
                .scalars()
                .all()
            ):
                chatbot[r.conversation_id] = {
                    "surface": str(r.surface or "dashboard"),
                    "customer_id": str(r.customer_id) if r.customer_id else None,
                    "chatbot_session_id": r.chatbot_session_id,
                }
            for r in (
                session.execute(
                    select(ConversationORM).where(ConversationORM.tenant_id == tenant_uuid).where(ConversationORM.id.in_(conv_ids))
                )
                .scalars()
                .all()
            ):
                whatsapp[r.id] = {
                    "customer_id": str(r.customer_id) if r.customer_id else None,
                    "assistant_session_id": r.assistant_session_id,
                }

    items: list[dict[str, object]] = []
    for r in rows:
        signals = signals_from_row(r)
        derived = derive_outcome(signals)
        chat_row = chatbot.get(r.conversation_id) or None
        wa_row = whatsapp.get(r.conversation_id) or None
        detected_surface = None
        if chat_row is not None:
            detected_surface = str(chat_row.get("surface") or "dashboard")
        elif wa_row is not None:
            detected_surface = "whatsapp"
        else:
            detected_surface = (r.channel or None) or "unknown"

        if surface and detected_surface != surface:
            continue
        if outcome and derived != outcome:
            continue

        items.append(
            {
                "conversation_id": str(r.conversation_id),
                "assistant_session_id": (
                    r.assistant_session_id
                    or (chat_row.get("chatbot_session_id") if chat_row is not None else None)
                    or (wa_row.get("assistant_session_id") if wa_row is not None else None)
                ),
                "surface": detected_surface,
                "channel": r.channel or None,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "last_activity_at": r.last_activity_at.isoformat() if r.last_activity_at else None,
                "abandoned_candidate": abandoned_candidate(last_activity_at=r.last_activity_at),
                "outcome": derived,
                "signals": {
                    "messages_received": signals.messages_received,
                    "messages_replied": signals.messages_replied,
                    "fallback": signals.fallback,
                    "handoff_created": signals.handoff_created,
                    "prebook_created": signals.prebook_created,
                    "conversion_confirmed": signals.conversion_confirmed,
                    "prebook_failed": signals.prebook_failed,
                    "missing_customer_identity": signals.missing_customer_identity,
                    "missing_customer_phone": signals.missing_customer_phone,
                    "operational_failed": signals.operational_failed,
                },
                "customer_id": ((chat_row.get("customer_id") if chat_row is not None else None) or (wa_row.get("customer_id") if wa_row is not None else None)),
            }
        )

    return {"from": start.isoformat(), "to": end.isoformat(), "tenant_id": str(tenant_uuid), "items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/assistant/conversations/{conversation_id}")
def assistant_conversation_details(
    conversation_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    """Conversation detail view for debugging/product analysis (tenant-scoped).

    Contains conversation text and should be treated as sensitive internal data.
    """
    tenant_uuid = uuid.UUID(require_tenant_id())
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise ValidationError("invalid_conversation_id")

    with db_session() as session:
        chat_sess = session.execute(
            select(ChatbotConversationSessionORM)
            .where(ChatbotConversationSessionORM.tenant_id == tenant_uuid)
            .where(ChatbotConversationSessionORM.conversation_id == conv_uuid)
        ).scalar_one_or_none()
        wa_sess = session.execute(
            select(ConversationORM).where(ConversationORM.tenant_id == tenant_uuid).where(ConversationORM.id == conv_uuid)
        ).scalar_one_or_none()

        ev_rows = (
            session.execute(
                select(AssistantFunnelEventORM)
                .where(AssistantFunnelEventORM.tenant_id == tenant_uuid)
                .where(AssistantFunnelEventORM.conversation_id == conv_uuid)
                .order_by(AssistantFunnelEventORM.created_at.asc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        # Turns: dashboard proxy uses chatbot_conversation_messages; WhatsApp uses messages + outbound_messages.
        turns: list[dict[str, object]] = []
        if chat_sess is not None:
            msg_rows = (
                session.execute(
                    select(ChatbotConversationMessageORM)
                    .where(ChatbotConversationMessageORM.tenant_id == tenant_uuid)
                    .where(ChatbotConversationMessageORM.conversation_id == conv_uuid)
                    .order_by(ChatbotConversationMessageORM.created_at.asc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            turns = [
                {
                    "role": r.role,
                    "source": "dashboard",
                    "content": r.content,
                    "intent": r.intent,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "meta": r.meta,
                }
                for r in msg_rows
            ]
        elif wa_sess is not None:
            inbound = (
                session.execute(
                    select(MessageORM)
                    .where(MessageORM.tenant_id == tenant_uuid)
                    .where(MessageORM.conversation_id == conv_uuid)
                    .order_by(MessageORM.created_at.asc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            outbound = (
                session.execute(
                    select(OutboundMessageORM)
                    .where(OutboundMessageORM.tenant_id == tenant_uuid)
                    .where(OutboundMessageORM.conversation_id == conv_uuid)
                    .order_by(OutboundMessageORM.created_at.asc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
            merged: list[tuple[datetime | None, dict[str, object]]] = []
            for m in inbound:
                merged.append(
                    (
                        m.created_at,
                        {
                            "role": "user",
                            "source": "whatsapp",
                            "content": m.body,
                            "created_at": m.created_at.isoformat() if m.created_at else None,
                            "meta": {"provider": m.provider, "provider_message_id": m.provider_message_id},
                        },
                    )
                )
            for m in outbound:
                merged.append(
                    (
                        m.created_at,
                        {
                            "role": "assistant",
                            "source": m.type or "outbound",
                            "content": m.rendered_body,
                            "created_at": m.created_at.isoformat() if m.created_at else None,
                            "meta": {"status": m.status, "delivery_status": m.delivery_status, "trace_id": m.trace_id},
                        },
                    )
                )
            merged.sort(key=lambda x: x[0] or datetime.min.replace(tzinfo=timezone.utc))
            turns = [item for _, item in merged[:limit]]

        # Derive signals/outcome from events.
        counts = {
            "messages_received": 0,
            "messages_replied": 0,
            "fallback": 0,
            "handoff_created": 0,
            "prebook_created": 0,
            "conversion_confirmed": 0,
            "prebook_failed": 0,
            "missing_customer_identity": 0,
            "missing_customer_phone": 0,
            "operational_failed": 0,
            "conversation_started": 0,
            "conversation_reset": 0,
        }
        for ev in ev_rows:
            name = (ev.event_name or "").strip()
            if name == ASSISTANT_MESSAGE_RECEIVED:
                counts["messages_received"] += 1
            elif name == ASSISTANT_MESSAGE_REPLIED:
                counts["messages_replied"] += 1
            elif name == ASSISTANT_FALLBACK:
                counts["fallback"] += 1
            elif name == ASSISTANT_HANDOFF_CREATED:
                counts["handoff_created"] += 1
            elif name == ASSISTANT_PREBOOK_CREATED:
                counts["prebook_created"] += 1
            elif name == ASSISTANT_CONVERSION_CONFIRMED:
                counts["conversion_confirmed"] += 1
            elif name == ASSISTANT_PREBOOK_FAILED:
                counts["prebook_failed"] += 1
            elif name == ASSISTANT_CUSTOMER_IDENTITY_MISSING:
                counts["missing_customer_identity"] += 1
            elif name == ASSISTANT_CUSTOMER_PHONE_MISSING:
                counts["missing_customer_phone"] += 1
            elif name == ASSISTANT_OPERATIONAL_FAILED:
                counts["operational_failed"] += 1
            elif name == ASSISTANT_CONVERSATION_STARTED:
                counts["conversation_started"] += 1
            elif name == ASSISTANT_CONVERSATION_RESET:
                counts["conversation_reset"] += 1

        signals = ConversationSignals(
            messages_received=counts["messages_received"],
            messages_replied=counts["messages_replied"],
            fallback=counts["fallback"],
            handoff_created=counts["handoff_created"],
            prebook_created=counts["prebook_created"],
            conversion_confirmed=counts["conversion_confirmed"],
            prebook_failed=counts["prebook_failed"],
            missing_customer_identity=counts["missing_customer_identity"],
            missing_customer_phone=counts["missing_customer_phone"],
            operational_failed=counts["operational_failed"],
        )

        started_at = ev_rows[0].created_at if ev_rows else None
        last_activity_at = ev_rows[-1].created_at if ev_rows else None
        outcome = derive_outcome(signals)

        events = [
            {
                "event_name": e.event_name,
                "trace_id": e.trace_id,
                "assistant_session_id": e.assistant_session_id,
                "channel": e.channel,
                "source": e.event_source,
                "meta": e.meta,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in ev_rows
        ]

        surface = "dashboard" if chat_sess is not None else ("whatsapp" if wa_sess is not None else "unknown")
        customer_id = (
            (str(chat_sess.customer_id) if chat_sess is not None and chat_sess.customer_id else None)
            or (str(wa_sess.customer_id) if wa_sess is not None and wa_sess.customer_id else None)
        )
        assistant_session_id = (
            (chat_sess.chatbot_session_id if chat_sess is not None else None)
            or (wa_sess.assistant_session_id if wa_sess is not None else None)
        )

    return {
        "tenant_id": str(tenant_uuid),
        "conversation_id": str(conv_uuid),
        "surface": surface,
        "customer_id": customer_id,
        "assistant_session_id": assistant_session_id,
        "started_at": started_at.isoformat() if started_at else None,
        "last_activity_at": last_activity_at.isoformat() if last_activity_at else None,
        "abandoned_candidate": abandoned_candidate(last_activity_at=last_activity_at),
        "outcome": outcome,
        "signals": counts,
        "turns": turns,
        "events": events,
    }


@router.get("/assistant/outcomes")
def assistant_outcomes(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    """Outcome counts for assistant conversations in a period (derived from funnel events)."""
    tenant_uuid = uuid.UUID(require_tenant_id())
    start, end = _validate_range(from_dt, to_dt)
    with db_session() as session:
        rows = session.execute(conversation_rollup_stmt(tenant_uuid=tenant_uuid, start=start, end=end)).all()
    counts: dict[str, int] = {}
    for r in rows:
        out = derive_outcome(signals_from_row(r))
        counts[out] = counts.get(out, 0) + 1
    items = [{"outcome": k, "count": int(v)} for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    return {"from": start.isoformat(), "to": end.isoformat(), "tenant_id": str(tenant_uuid), "items": items}
