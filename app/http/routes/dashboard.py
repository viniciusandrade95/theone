import uuid
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func, select

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.tenancy import require_tenant_id
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.tenants.repo.settings_sql import SqlTenantSettingsRepo

router = APIRouter()

_FINAL_APPOINTMENT_STATUSES = ("completed", "cancelled", "no_show")


def _coerce_uuid(value: str):
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return str(value)


def _tenant_timezone(session, tenant_id: str) -> str:
    settings = SqlTenantSettingsRepo(session).get_or_create(tenant_id=tenant_id)
    timezone_name = settings.default_timezone or "UTC"
    try:
        ZoneInfo(timezone_name)
        return timezone_name
    except ZoneInfoNotFoundError:
        return "UTC"


def _local_day_bounds(now_utc: datetime, tz_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    local_now = now_utc.astimezone(tz)
    local_start = datetime.combine(local_now.date(), time.min).replace(tzinfo=tz)
    local_end = local_start + timedelta(days=1)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


class DashboardCounts(BaseModel):
    appointments_today_count: int = 0
    appointments_pending_confirmation_count: int = 0
    tasks_today_count: int = 0
    inactive_customers_count: int = 0
    scheduled_reminders_count: int = 0
    recent_no_shows_count: int = 0
    new_online_bookings_count: int = 0


class DashboardAppointmentItem(BaseModel):
    id: str
    created_at: datetime
    starts_at: datetime
    ends_at: datetime
    status: str
    needs_confirmation: bool
    customer_id: str
    customer_name: str
    service_id: str | None
    service_name: str | None
    location_id: str
    location_name: str


class InactiveCustomerItem(BaseModel):
    id: str
    name: str
    phone: str | None
    email: str | None
    last_completed_at: datetime | None = None


class DashboardSections(BaseModel):
    appointments_today: list[DashboardAppointmentItem] = Field(default_factory=list)
    appointments_pending_confirmation: list[DashboardAppointmentItem] = Field(default_factory=list)
    tasks_today: list[dict] = Field(default_factory=list)
    inactive_customers: list[InactiveCustomerItem] = Field(default_factory=list)
    scheduled_reminders: list[dict] = Field(default_factory=list)
    recent_no_shows: list[DashboardAppointmentItem] = Field(default_factory=list)
    new_online_bookings: list[DashboardAppointmentItem] = Field(default_factory=list)


class DashboardOverviewOut(BaseModel):
    timezone: str
    today_start_utc: datetime
    today_end_utc: datetime
    counts: DashboardCounts
    sections: DashboardSections
    notes: list[str] = Field(default_factory=list)


def _appointment_item_stmt(tenant_key, *, where_filters, order_by, limit: int):
    return (
        select(
            AppointmentORM.id.label("id"),
            AppointmentORM.created_at.label("created_at"),
            AppointmentORM.starts_at.label("starts_at"),
            AppointmentORM.ends_at.label("ends_at"),
            AppointmentORM.status.label("status"),
            AppointmentORM.needs_confirmation.label("needs_confirmation"),
            CustomerORM.id.label("customer_id"),
            CustomerORM.name.label("customer_name"),
            ServiceORM.id.label("service_id"),
            ServiceORM.name.label("service_name"),
            LocationORM.id.label("location_id"),
            LocationORM.name.label("location_name"),
        )
        .select_from(AppointmentORM)
        .join(
            CustomerORM,
            and_(
                CustomerORM.id == AppointmentORM.customer_id,
                CustomerORM.tenant_id == tenant_key,
                CustomerORM.deleted_at.is_(None),
            ),
        )
        .join(
            LocationORM,
            and_(
                LocationORM.id == AppointmentORM.location_id,
                LocationORM.tenant_id == tenant_key,
                LocationORM.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            ServiceORM,
            and_(
                ServiceORM.id == AppointmentORM.service_id,
                ServiceORM.tenant_id == tenant_key,
                ServiceORM.deleted_at.is_(None),
            ),
        )
        .where(AppointmentORM.tenant_id == tenant_key)
        .where(AppointmentORM.deleted_at.is_(None))
        .where(*where_filters)
        .order_by(*order_by)
        .limit(limit)
    )


def _rows_to_appointment_items(rows) -> list[DashboardAppointmentItem]:
    return [
        DashboardAppointmentItem(
            id=str(row.id),
            created_at=row.created_at,
            starts_at=row.starts_at,
            ends_at=row.ends_at,
            status=row.status,
            needs_confirmation=bool(row.needs_confirmation),
            customer_id=str(row.customer_id),
            customer_name=row.customer_name,
            service_id=str(row.service_id) if row.service_id is not None else None,
            service_name=row.service_name,
            location_id=str(row.location_id),
            location_name=row.location_name,
        )
        for row in rows
    ]


@router.get("/dashboard/overview", response_model=DashboardOverviewOut)
def dashboard_overview(_tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    tenant_key = _coerce_uuid(tenant_id)
    now_utc = datetime.now(timezone.utc)

    with db_session() as session:
        tz_name = _tenant_timezone(session, tenant_id=tenant_id)
        today_start_utc, today_end_utc = _local_day_bounds(now_utc, tz_name)

        no_show_cutoff = now_utc - timedelta(days=14)

        appointments_today_case = case(
            (
                and_(
                    AppointmentORM.starts_at >= today_start_utc,
                    AppointmentORM.starts_at < today_end_utc,
                    AppointmentORM.status.notin_(_FINAL_APPOINTMENT_STATUSES),
                ),
                1,
            ),
            else_=0,
        )
        pending_confirmation_case = case(
            (
                and_(
                    AppointmentORM.needs_confirmation.is_(True),
                    AppointmentORM.status.notin_(_FINAL_APPOINTMENT_STATUSES),
                    AppointmentORM.starts_at >= now_utc,
                ),
                1,
            ),
            else_=0,
        )
        recent_no_show_case = case(
            (
                and_(
                    AppointmentORM.status == "no_show",
                    AppointmentORM.status_updated_at >= no_show_cutoff,
                ),
                1,
            ),
            else_=0,
        )
        new_online_bookings_case = case(
            (
                and_(
                    AppointmentORM.created_by_user_id.is_(None),
                    AppointmentORM.created_at >= today_start_utc,
                    AppointmentORM.created_at < today_end_utc,
                ),
                1,
            ),
            else_=0,
        )

        aggregate_stmt = (
            select(
                func.sum(appointments_today_case).label("appointments_today_count"),
                func.sum(pending_confirmation_case).label("appointments_pending_confirmation_count"),
                func.sum(recent_no_show_case).label("recent_no_shows_count"),
                func.sum(new_online_bookings_case).label("new_online_bookings_count"),
            )
            .select_from(AppointmentORM)
            .where(AppointmentORM.tenant_id == tenant_key)
            .where(AppointmentORM.deleted_at.is_(None))
        )
        aggregate = session.execute(aggregate_stmt).one()

        appointments_today = _rows_to_appointment_items(
            session.execute(
                _appointment_item_stmt(
                    tenant_key,
                    where_filters=[
                        AppointmentORM.starts_at >= today_start_utc,
                        AppointmentORM.starts_at < today_end_utc,
                        AppointmentORM.status.notin_(_FINAL_APPOINTMENT_STATUSES),
                    ],
                    order_by=[AppointmentORM.starts_at.asc(), AppointmentORM.id.asc()],
                    limit=5,
                )
            ).all()
        )

        appointments_pending_confirmation = _rows_to_appointment_items(
            session.execute(
                _appointment_item_stmt(
                    tenant_key,
                    where_filters=[
                        AppointmentORM.needs_confirmation.is_(True),
                        AppointmentORM.status.notin_(_FINAL_APPOINTMENT_STATUSES),
                        AppointmentORM.starts_at >= now_utc,
                    ],
                    order_by=[AppointmentORM.starts_at.asc(), AppointmentORM.id.asc()],
                    limit=5,
                )
            ).all()
        )

        recent_no_shows = _rows_to_appointment_items(
            session.execute(
                _appointment_item_stmt(
                    tenant_key,
                    where_filters=[
                        AppointmentORM.status == "no_show",
                        AppointmentORM.status_updated_at >= no_show_cutoff,
                    ],
                    order_by=[AppointmentORM.status_updated_at.desc(), AppointmentORM.id.desc()],
                    limit=5,
                )
            ).all()
        )

        new_online_bookings = _rows_to_appointment_items(
            session.execute(
                _appointment_item_stmt(
                    tenant_key,
                    where_filters=[
                        AppointmentORM.created_by_user_id.is_(None),
                        AppointmentORM.created_at >= today_start_utc,
                        AppointmentORM.created_at < today_end_utc,
                    ],
                    order_by=[AppointmentORM.created_at.desc(), AppointmentORM.id.desc()],
                    limit=5,
                )
            ).all()
        )

        last_completed_subq = (
            select(
                AppointmentORM.customer_id.label("customer_id"),
                func.max(AppointmentORM.starts_at).label("last_completed_at"),
            )
            .where(AppointmentORM.tenant_id == tenant_key)
            .where(AppointmentORM.deleted_at.is_(None))
            .where(AppointmentORM.status == "completed")
            .group_by(AppointmentORM.customer_id)
            .subquery()
        )
        inactive_cutoff = now_utc - timedelta(days=60)
        inactive_sort_key = case((last_completed_subq.c.last_completed_at.is_(None), 0), else_=1)
        inactive_customers_stmt = (
            select(
                CustomerORM.id.label("id"),
                CustomerORM.name.label("name"),
                CustomerORM.phone.label("phone"),
                CustomerORM.email.label("email"),
                last_completed_subq.c.last_completed_at.label("last_completed_at"),
            )
            .select_from(CustomerORM)
            .outerjoin(last_completed_subq, last_completed_subq.c.customer_id == CustomerORM.id)
            .where(CustomerORM.tenant_id == tenant_key)
            .where(CustomerORM.deleted_at.is_(None))
            .where(
                case(
                    (last_completed_subq.c.last_completed_at.is_(None), True),
                    else_=last_completed_subq.c.last_completed_at < inactive_cutoff,
                )
            )
            .order_by(inactive_sort_key.asc(), last_completed_subq.c.last_completed_at.asc(), CustomerORM.created_at.asc())
            .limit(5)
        )
        inactive_customers_rows = session.execute(inactive_customers_stmt).all()
        inactive_customers = [
            InactiveCustomerItem(
                id=str(row.id),
                name=row.name,
                phone=row.phone,
                email=row.email,
                last_completed_at=row.last_completed_at,
            )
            for row in inactive_customers_rows
        ]

        inactive_customers_count_stmt = (
            select(func.count())
            .select_from(CustomerORM)
            .outerjoin(last_completed_subq, last_completed_subq.c.customer_id == CustomerORM.id)
            .where(CustomerORM.tenant_id == tenant_key)
            .where(CustomerORM.deleted_at.is_(None))
            .where(
                case(
                    (last_completed_subq.c.last_completed_at.is_(None), True),
                    else_=last_completed_subq.c.last_completed_at < inactive_cutoff,
                )
            )
        )
        inactive_customers_count = int(session.execute(inactive_customers_count_stmt).scalar_one() or 0)

        counts = DashboardCounts(
            appointments_today_count=int(aggregate.appointments_today_count or 0),
            appointments_pending_confirmation_count=int(aggregate.appointments_pending_confirmation_count or 0),
            tasks_today_count=0,
            inactive_customers_count=inactive_customers_count,
            scheduled_reminders_count=0,
            recent_no_shows_count=int(aggregate.recent_no_shows_count or 0),
            new_online_bookings_count=int(aggregate.new_online_bookings_count or 0),
        )

        notes = [
            "Tasks and reminders are not implemented yet; this MVP returns honest empty states.",
            "New online bookings today uses a proxy: appointments with created_by_user_id = NULL and created_at within tenant 'today' window.",
            "Recent no-shows uses a 14-day cutoff based on status_updated_at.",
        ]

        return DashboardOverviewOut(
            timezone=tz_name,
            today_start_utc=today_start_utc,
            today_end_utc=today_end_utc,
            counts=counts,
            sections=DashboardSections(
                appointments_today=appointments_today,
                appointments_pending_confirmation=appointments_pending_confirmation,
                tasks_today=[],
                inactive_customers=inactive_customers,
                scheduled_reminders=[],
                recent_no_shows=recent_no_shows,
                new_online_bookings=new_online_bookings,
            ),
            notes=notes,
        )
