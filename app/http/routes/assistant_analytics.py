import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, distinct, func, select

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.errors import ValidationError
from core.tenancy import require_tenant_id
from modules.assistant.models.funnel_event_orm import AssistantFunnelEventORM
from modules.assistant.service.funnel_events import (
    ASSISTANT_CONVERSION_CONFIRMED,
    ASSISTANT_FALLBACK,
    ASSISTANT_HANDOFF_CREATED,
    ASSISTANT_HANDOFF_REQUESTED,
    ASSISTANT_MESSAGE_RECEIVED,
    ASSISTANT_MESSAGE_REPLIED,
    ASSISTANT_PREBOOK_CREATED,
    ASSISTANT_PREBOOK_REQUESTED,
)
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

