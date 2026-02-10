import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, case, distinct, func, select

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.errors import ValidationError
from core.tenancy import require_tenant_id
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.service_orm import ServiceORM
from modules.tenants.repo.settings_sql import SqlTenantSettingsRepo

router = APIRouter()


def _parse_dt(s: str) -> datetime:
    s = (s or "").strip().replace(" ", "+")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        raise ValidationError("Invalid datetime format. Use ISO 8601, e.g. 2026-01-17T00:00:00+00:00")


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _coerce_uuid(value: str):
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return str(value)


def _parse_location_id(location_id: str | None):
    if location_id is None:
        return None
    try:
        return uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid location_id")


def _validate_range(from_dt: datetime, to_dt: datetime) -> tuple[datetime, datetime]:
    start = _to_utc(from_dt)
    end = _to_utc(to_dt)
    if start >= end:
        raise HTTPException(status_code=400, detail="'from' must be before 'to'")
    return start, end


def _appointment_filters(tenant_key, from_dt: datetime, to_dt: datetime, location_key=None):
    filters = [
        AppointmentORM.tenant_id == tenant_key,
        AppointmentORM.deleted_at.is_(None),
        AppointmentORM.starts_at >= from_dt,
        AppointmentORM.starts_at < to_dt,
    ]
    if location_key is not None:
        filters.append(AppointmentORM.location_id == location_key)
    return filters


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _tenant_timezone(session, tenant_id: str) -> str:
    settings = SqlTenantSettingsRepo(session).get_or_create(tenant_id=tenant_id)
    timezone_name = settings.default_timezone or "UTC"
    try:
        ZoneInfo(timezone_name)
        return timezone_name
    except ZoneInfoNotFoundError:
        return "UTC"


@router.get("/summary")
def summary(start: str, end: str, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    s = c.analytics.summary(start=_parse_dt(start), end=_parse_dt(end))
    return s.__dict__


@router.get("/overview")
def overview(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    location_id: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = require_tenant_id()
    tenant_key = _coerce_uuid(tenant_id)
    location_key = _coerce_uuid(_parse_location_id(location_id)) if location_id else None
    start, end = _validate_range(from_dt, to_dt)

    with db_session() as session:
        filters = _appointment_filters(tenant_key, start, end, location_key)
        aggregate_stmt = select(
            func.count(AppointmentORM.id).label("total_appointments"),
            func.sum(case((AppointmentORM.status == "completed", 1), else_=0)).label("completed_count"),
            func.sum(case((AppointmentORM.status == "cancelled", 1), else_=0)).label("cancelled_count"),
            func.sum(case((AppointmentORM.status == "no_show", 1), else_=0)).label("no_show_count"),
        ).where(*filters)
        aggregate = session.execute(aggregate_stmt).one()

        total_appointments = int(aggregate.total_appointments or 0)
        completed_count = int(aggregate.completed_count or 0)
        cancelled_count = int(aggregate.cancelled_count or 0)
        no_show_count = int(aggregate.no_show_count or 0)

        unique_customers_stmt = select(func.count(distinct(AppointmentORM.customer_id))).where(*filters)
        unique_customers = int(session.execute(unique_customers_stmt).scalar_one() or 0)

        new_customers_stmt = (
            select(func.count(distinct(AppointmentORM.customer_id)))
            .select_from(AppointmentORM)
            .join(
                CustomerORM,
                and_(
                    CustomerORM.id == AppointmentORM.customer_id,
                    CustomerORM.tenant_id == tenant_key,
                ),
            )
            .where(*filters)
            .where(CustomerORM.deleted_at.is_(None))
            .where(CustomerORM.created_at >= start)
            .where(CustomerORM.created_at < end)
        )
        new_customers = int(session.execute(new_customers_stmt).scalar_one() or 0)
        returning_customers = max(unique_customers - new_customers, 0)
        repeat_rate = _ratio(returning_customers, unique_customers)

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "location_id": str(location_key) if location_key is not None else None,
        "total_appointments_created": total_appointments,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "no_show_count": no_show_count,
        "completion_rate": _ratio(completed_count, total_appointments),
        "cancellation_rate": _ratio(cancelled_count, total_appointments),
        "no_show_rate": _ratio(no_show_count, total_appointments),
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "repeat_rate": repeat_rate,
        "status_breakdown": {
            "booked": max(total_appointments - completed_count - cancelled_count - no_show_count, 0),
            "completed": completed_count,
            "cancelled": cancelled_count,
            "no_show": no_show_count,
        },
    }


@router.get("/services")
def services_breakdown(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    location_id: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = require_tenant_id()
    tenant_key = _coerce_uuid(tenant_id)
    location_key = _coerce_uuid(_parse_location_id(location_id)) if location_id else None
    start, end = _validate_range(from_dt, to_dt)

    with db_session() as session:
        filters = _appointment_filters(tenant_key, start, end, location_key)
        stmt = (
            select(
                AppointmentORM.service_id.label("service_id"),
                ServiceORM.name.label("service_name"),
                func.count(AppointmentORM.id).label("bookings"),
            )
            .select_from(AppointmentORM)
            .outerjoin(
                ServiceORM,
                and_(
                    ServiceORM.id == AppointmentORM.service_id,
                    ServiceORM.tenant_id == tenant_key,
                    ServiceORM.deleted_at.is_(None),
                ),
            )
            .where(*filters)
            .group_by(AppointmentORM.service_id, ServiceORM.name)
            .order_by(func.count(AppointmentORM.id).desc(), ServiceORM.name.asc())
        )
        rows = session.execute(stmt).all()

    items: list[dict] = []
    total_bookings = 0
    for row in rows:
        bookings = int(row.bookings or 0)
        total_bookings += bookings
        items.append(
            {
                "service_id": str(row.service_id) if row.service_id is not None else None,
                "service_name": row.service_name or "Unassigned",
                "bookings": bookings,
            }
        )

    service_mix = [
        {
            **item,
            "share": _ratio(item["bookings"], total_bookings),
        }
        for item in items
    ]

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "location_id": str(location_key) if location_key is not None else None,
        "total_bookings": total_bookings,
        "top_services": service_mix[:10],
        "service_mix": service_mix,
    }


@router.get("/heatmap")
def heatmap(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    location_id: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = require_tenant_id()
    tenant_key = _coerce_uuid(tenant_id)
    location_key = _coerce_uuid(_parse_location_id(location_id)) if location_id else None
    start, end = _validate_range(from_dt, to_dt)

    weekdays = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    heatmap_counts = {(weekday, hour): 0 for weekday in weekdays for hour in range(24)}

    with db_session() as session:
        timezone_name = _tenant_timezone(session, tenant_id)
        tenant_tz = ZoneInfo(timezone_name)
        filters = _appointment_filters(tenant_key, start, end, location_key)
        stmt = select(AppointmentORM.starts_at).where(*filters)
        starts = list(session.execute(stmt).scalars().all())

    for starts_at in starts:
        if starts_at is None:
            continue
        normalized = starts_at if starts_at.tzinfo is not None else starts_at.replace(tzinfo=timezone.utc)
        local = normalized.astimezone(tenant_tz)
        heatmap_counts[(weekdays[local.weekday()], local.hour)] += 1

    items = [
        {"weekday": weekday, "hour": hour, "count": heatmap_counts[(weekday, hour)]}
        for weekday in weekdays
        for hour in range(24)
    ]

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "location_id": str(location_key) if location_key is not None else None,
        "timezone": timezone_name,
        "items": items,
    }


@router.get("/bookings_over_time")
def bookings_over_time(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    location_id: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = require_tenant_id()
    tenant_key = _coerce_uuid(tenant_id)
    location_key = _coerce_uuid(_parse_location_id(location_id)) if location_id else None
    start, end = _validate_range(from_dt, to_dt)

    with db_session() as session:
        timezone_name = _tenant_timezone(session, tenant_id)
        tenant_tz = ZoneInfo(timezone_name)
        filters = _appointment_filters(tenant_key, start, end, location_key)
        stmt = select(AppointmentORM.starts_at).where(*filters)
        starts = list(session.execute(stmt).scalars().all())

    local_start = start.astimezone(tenant_tz).date()
    local_end = (end - timedelta(microseconds=1)).astimezone(tenant_tz).date()
    if local_end < local_start:
        local_end = local_start

    counts_by_day: dict[date, int] = {}
    cursor = local_start
    while cursor <= local_end:
        counts_by_day[cursor] = 0
        cursor += timedelta(days=1)

    for starts_at in starts:
        if starts_at is None:
            continue
        normalized = starts_at if starts_at.tzinfo is not None else starts_at.replace(tzinfo=timezone.utc)
        local_day = normalized.astimezone(tenant_tz).date()
        counts_by_day[local_day] = counts_by_day.get(local_day, 0) + 1

    items = [
        {
            "date": day.isoformat(),
            "count": count,
        }
        for day, count in sorted(counts_by_day.items())
    ]

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "location_id": str(location_key) if location_key is not None else None,
        "timezone": timezone_name,
        "items": items,
    }


@router.get("/at_risk")
def at_risk_customers(
    from_dt: datetime = Query(..., alias="from"),
    to_dt: datetime = Query(..., alias="to"),
    threshold_days: int = Query(default=45, ge=1, le=365),
    location_id: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = require_tenant_id()
    tenant_key = _coerce_uuid(tenant_id)
    location_key = _coerce_uuid(_parse_location_id(location_id)) if location_id else None
    _, end = _validate_range(from_dt, to_dt)
    cutoff = end - timedelta(days=threshold_days)

    with db_session() as session:
        last_appointment_subquery = (
            select(
                AppointmentORM.customer_id.label("customer_id"),
                func.max(AppointmentORM.starts_at).label("last_appointment_at"),
            )
            .where(AppointmentORM.tenant_id == tenant_key)
            .where(AppointmentORM.deleted_at.is_(None))
        )
        if location_key is not None:
            last_appointment_subquery = last_appointment_subquery.where(AppointmentORM.location_id == location_key)
        last_appointment_subquery = last_appointment_subquery.group_by(AppointmentORM.customer_id).subquery()

        stmt = (
            select(
                CustomerORM.id.label("customer_id"),
                CustomerORM.name.label("customer_name"),
                CustomerORM.phone.label("customer_phone"),
                CustomerORM.email.label("customer_email"),
                last_appointment_subquery.c.last_appointment_at.label("last_appointment_at"),
            )
            .select_from(CustomerORM)
            .join(last_appointment_subquery, last_appointment_subquery.c.customer_id == CustomerORM.id)
            .where(CustomerORM.tenant_id == tenant_key)
            .where(CustomerORM.deleted_at.is_(None))
            .where(last_appointment_subquery.c.last_appointment_at < cutoff)
            .order_by(last_appointment_subquery.c.last_appointment_at.asc(), CustomerORM.name.asc())
            .limit(200)
        )
        rows = session.execute(stmt).all()

    items = []
    for row in rows:
        last_appointment_at = row.last_appointment_at
        normalized_last = (
            last_appointment_at
            if last_appointment_at.tzinfo is not None
            else last_appointment_at.replace(tzinfo=timezone.utc)
        )
        items.append(
            {
                "customer_id": str(row.customer_id),
                "customer_name": row.customer_name,
                "customer_phone": row.customer_phone,
                "customer_email": row.customer_email,
                "last_appointment_at": normalized_last.isoformat(),
                "days_since_last_appointment": max((end - normalized_last).days, 0),
            }
        )

    return {
        "threshold_days": threshold_days,
        "reference_at": end.isoformat(),
        "location_id": str(location_key) if location_key is not None else None,
        "items": items,
    }
