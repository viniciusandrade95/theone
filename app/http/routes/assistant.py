import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import func, select

from app.http.deps import require_assistant_token, require_tenant_header
from core.db.session import db_session
from core.errors import ValidationError
from core.tenancy import require_tenant_id

from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.crm.repo_appointments import AppointmentCreate, AppointmentOverlapError, AppointmentsRepo
from modules.crm.repo_locations import LocationsRepo
from modules.tenants.repo.settings_sql import SqlTenantSettingsRepo


router = APIRouter()


DEFAULT_ASSISTANT_APPOINTMENT_NOTES = "criado pelo assistant"


def _ensure_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise ValidationError("invalid_timezone", meta={"timezone": tz_name})


def _resolve_default_location(session, *, tenant_id: str) -> LocationORM:
    settings_repo = SqlTenantSettingsRepo(session)
    locations_repo = LocationsRepo(session)

    settings = settings_repo.get_or_create(tenant_id=tenant_id)
    if settings.default_location_id is not None:
        location = locations_repo.get_location(tenant_id=tenant_id, location_id=str(settings.default_location_id))
        if location is not None and location.deleted_at is None and location.is_active:
            return location

    location = locations_repo.ensure_default_location(tenant_id=tenant_id, default_timezone=settings.default_timezone)
    if settings.default_location_id != location.id:
        settings_repo.update(tenant_id=tenant_id, patch={"default_location_id": str(location.id)})
    return location


class AssistantCustomerIn(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def _validate_customer(self):
        phone = (self.phone or "").strip()
        email = str(self.email).strip() if self.email else ""
        if not phone and not email:
            raise ValueError("Provide customer.phone and/or customer.email")
        return self


class AssistantBookingIn(BaseModel):
    service_id: uuid.UUID | None = None
    service_name: str | None = Field(default=None, max_length=255)
    location_id: uuid.UUID | None = None
    requested_date: date | None = None
    requested_time: time | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_booking(self):
        if self.service_id is None and not (self.service_name or "").strip():
            raise ValueError("Provide booking.service_id or booking.service_name")
        if self.starts_at is None:
            if self.requested_date is None or self.requested_time is None:
                raise ValueError("Provide booking.starts_at or (booking.requested_date + booking.requested_time)")
        return self


class AssistantPrebookIn(BaseModel):
    customer: AssistantCustomerIn
    booking: AssistantBookingIn


class AssistantPrebookDataOut(BaseModel):
    appointment_id: str
    customer_id: str
    service_id: str
    location_id: str
    starts_at: datetime
    ends_at: datetime


class AssistantPrebookOut(BaseModel):
    ok: bool
    reference: str
    status: Literal["created", "existing"]
    message: str
    trace_id: str
    data: AssistantPrebookDataOut


def _ref_for(appointment_id: uuid.UUID) -> str:
    return f"PB-{str(appointment_id).split('-')[0].upper()}"


def _resolve_customer(session, request: Request, *, tenant_uuid: uuid.UUID, payload: AssistantCustomerIn) -> uuid.UUID:
    phone = (payload.phone or "").strip()
    email = str(payload.email).strip().lower() if payload.email else None

    customer_by_phone = None
    if phone:
        stmt = (
            select(CustomerORM)
            .where(CustomerORM.tenant_id == tenant_uuid)
            .where(CustomerORM.phone == phone)
            .where(CustomerORM.deleted_at.is_(None))
        )
        customer_by_phone = session.execute(stmt).scalar_one_or_none()

    customer_by_email = None
    if email:
        stmt = (
            select(CustomerORM)
            .where(CustomerORM.tenant_id == tenant_uuid)
            .where(CustomerORM.email == email)
            .where(CustomerORM.deleted_at.is_(None))
        )
        customer_by_email = session.execute(stmt).scalar_one_or_none()

    if customer_by_phone and customer_by_email and customer_by_phone.id != customer_by_email.id:
        raise ValidationError("customer_identity_conflict", meta={"phone": phone, "email": email})

    existing = customer_by_phone or customer_by_email
    if existing is not None:
        return existing.id

    name = (payload.name or "").strip()
    if not name:
        raise ValidationError("customer_name_required", meta={"phone": phone or None, "email": email})

    container = request.app.state.container
    created = container.crm.create_customer(
        name=name,
        phone=phone or None,
        email=email,
    )
    try:
        return uuid.UUID(created.id)
    except ValueError:
        raise ValidationError("invalid_customer_id_created")


def _resolve_service(session, *, tenant_uuid: uuid.UUID, booking: AssistantBookingIn) -> ServiceORM:
    if booking.service_id is not None:
        stmt = (
            select(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_uuid)
            .where(ServiceORM.id == booking.service_id)
            .where(ServiceORM.deleted_at.is_(None))
            .where(ServiceORM.is_active.is_(True))
        )
        svc = session.execute(stmt).scalar_one_or_none()
        if svc is None:
            raise ValidationError("service_not_found_or_inactive", meta={"service_id": str(booking.service_id)})
        return svc

    desired_name = (booking.service_name or "").strip()
    desired_key = desired_name.lower()
    stmt = (
        select(ServiceORM)
        .where(ServiceORM.tenant_id == tenant_uuid)
        .where(ServiceORM.deleted_at.is_(None))
        .where(ServiceORM.is_active.is_(True))
        .where(func.lower(ServiceORM.name) == desired_key)
    )
    matches = list(session.execute(stmt).scalars().all())
    if not matches:
        raise ValidationError("service_not_found", meta={"service_name": desired_name})
    if len(matches) > 1:
        raise ValidationError(
            "service_ambiguous",
            meta={
                "service_name": desired_name,
                "count": len(matches),
                "matches": [{"id": str(s.id), "name": s.name} for s in matches[:3]],
            },
        )
    return matches[0]


def _resolve_location(session, *, tenant_id: str, tenant_uuid: uuid.UUID, location_id: uuid.UUID | None) -> LocationORM:
    if location_id is None:
        return _resolve_default_location(session, tenant_id=tenant_id)
    stmt = (
        select(LocationORM)
        .where(LocationORM.tenant_id == tenant_uuid)
        .where(LocationORM.id == location_id)
        .where(LocationORM.deleted_at.is_(None))
        .where(LocationORM.is_active.is_(True))
    )
    loc = session.execute(stmt).scalar_one_or_none()
    if loc is None:
        raise ValidationError("location_not_found", meta={"location_id": str(location_id)})
    return loc


def _resolve_window(*, booking: AssistantBookingIn, service: ServiceORM, location: LocationORM) -> tuple[datetime, datetime]:
    duration_min = int(service.duration_minutes)
    now_utc = datetime.now(timezone.utc)

    if booking.starts_at is not None:
        if booking.starts_at.tzinfo is None:
            raise ValidationError("starts_at_must_be_timezone_aware")
        starts_utc = booking.starts_at.astimezone(timezone.utc)
        ends = booking.ends_at
        if ends is None:
            ends_utc = starts_utc + timedelta(minutes=duration_min)
        else:
            if ends.tzinfo is None:
                raise ValidationError("ends_at_must_be_timezone_aware")
            ends_utc = ends.astimezone(timezone.utc)
    else:
        tz = _ensure_tz(location.timezone)
        local = datetime.combine(booking.requested_date, booking.requested_time, tzinfo=tz)  # type: ignore[arg-type]
        starts_utc = local.astimezone(timezone.utc)
        ends_utc = (local + timedelta(minutes=duration_min)).astimezone(timezone.utc)

    if starts_utc >= ends_utc:
        raise ValidationError("invalid_time_window", meta={"starts_at": starts_utc.isoformat(), "ends_at": ends_utc.isoformat()})
    if starts_utc < (now_utc - timedelta(minutes=1)):
        raise ValidationError("starts_at_in_past", meta={"starts_at": starts_utc.isoformat()})
    return starts_utc, ends_utc


def _find_existing_appointment(
    session,
    *,
    tenant_uuid: uuid.UUID,
    customer_id: uuid.UUID,
    location_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
) -> AppointmentORM | None:
    stmt = (
        select(AppointmentORM)
        .where(AppointmentORM.tenant_id == tenant_uuid)
        .where(AppointmentORM.customer_id == customer_id)
        .where(AppointmentORM.location_id == location_id)
        .where(AppointmentORM.deleted_at.is_(None))
        .where(AppointmentORM.status != "cancelled")
        .where(AppointmentORM.starts_at == starts_at)
        .where(AppointmentORM.ends_at == ends_at)
        .order_by(AppointmentORM.created_at.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


@router.post("/assistant/prebook", response_model=AssistantPrebookOut, status_code=201)
def prebook(
    payload: AssistantPrebookIn,
    request: Request,
    response: Response,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    _tenant=Depends(require_tenant_header),
    _auth=Depends(require_assistant_token),
):
    tenant_id = require_tenant_id()
    effective_trace_id = x_trace_id or str(uuid.uuid4())

    with db_session() as session:
        container = request.app.state.container
        container.tenant_service.get_or_fail(tenant_id)

        tenant_uuid = uuid.UUID(tenant_id)

        customer_id = _resolve_customer(session, request, tenant_uuid=tenant_uuid, payload=payload.customer)
        location = _resolve_location(
            session,
            tenant_id=tenant_id,
            tenant_uuid=tenant_uuid,
            location_id=payload.booking.location_id,
        )
        service = _resolve_service(session, tenant_uuid=tenant_uuid, booking=payload.booking)
        starts_utc, ends_utc = _resolve_window(booking=payload.booking, service=service, location=location)

        existing = _find_existing_appointment(
            session,
            tenant_uuid=tenant_uuid,
            customer_id=customer_id,
            location_id=location.id,
            starts_at=starts_utc,
            ends_at=ends_utc,
        )
        if existing is not None:
            response.status_code = 200
            return AssistantPrebookOut(
                ok=True,
                reference=_ref_for(existing.id),
                status="existing",
                message="Appointment already exists for this customer and slot.",
                trace_id=effective_trace_id,
                data=AssistantPrebookDataOut(
                    appointment_id=str(existing.id),
                    customer_id=str(existing.customer_id),
                    service_id=str(existing.service_id) if existing.service_id else "",
                    location_id=str(existing.location_id),
                    starts_at=existing.starts_at,
                    ends_at=existing.ends_at,
                ),
            )

        repo = AppointmentsRepo(session)
        try:
            appointment = repo.create(
                tenant_uuid,
                AppointmentCreate(
                    customer_id=customer_id,
                    location_id=location.id,
                    service_id=service.id,
                    starts_at=starts_utc,
                    ends_at=ends_utc,
                    status="pending",
                    needs_confirmation=True,
                    notes=DEFAULT_ASSISTANT_APPOINTMENT_NOTES,
                    created_by_user_id=None,
                    updated_by_user_id=None,
                ),
            )
        except AppointmentOverlapError as err:
            return JSONResponse(status_code=409, content={"error": "APPOINTMENT_OVERLAP", "conflicts": err.conflicts})

        return AssistantPrebookOut(
            ok=True,
            reference=_ref_for(appointment.id),
            status="created",
            message="Prebooking created successfully.",
            trace_id=effective_trace_id,
            data=AssistantPrebookDataOut(
                appointment_id=str(appointment.id),
                customer_id=str(customer_id),
                service_id=str(service.id),
                location_id=str(location.id),
                starts_at=starts_utc,
                ends_at=ends_utc,
            ),
        )

