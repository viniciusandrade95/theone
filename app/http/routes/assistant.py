import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import select

from app.http.deps import require_tenant_header, require_user_or_assistant_connector
from core.errors import ConflictError, NotFoundError, ValidationError
from core.tenancy import require_tenant_id
from core.db.session import db_session

from modules.assistant.repo.prebook_request_repo import AssistantPrebookRequestRepo
from modules.chatbot.repo.session_repo import ChatbotSessionRepo
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.crm.repo_appointments import AppointmentCreate, AppointmentOverlapError, AppointmentsRepo
from modules.iam.models.user_orm import UserORM
from modules.tenants.repo.settings_sql import SqlTenantSettingsRepo
from modules.crm.repo_locations import LocationsRepo


router = APIRouter()


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
    customer_id: uuid.UUID | None = None
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def _validate_customer(self):
        if self.customer_id is not None:
            return self
        if not self.name or not self.name.strip():
            raise ValueError("customer.name is required when customer_id is not provided")
        if not self.phone or not self.phone.strip():
            raise ValueError("customer.phone is required when customer_id is not provided")
        return self


class AssistantBookingIn(BaseModel):
    service_id: uuid.UUID
    location_id: uuid.UUID | None = None
    requested_date: date | None = None
    requested_time: time | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def _validate_booking(self):
        if self.starts_at is None:
            if self.requested_date is None or self.requested_time is None:
                raise ValueError("Provide booking.starts_at or (booking.requested_date + booking.requested_time)")
        return self


class AssistantMetaIn(BaseModel):
    surface: str = Field(default="dashboard", max_length=64)
    actor_type: Literal["staff", "system"] = "staff"
    actor_id: uuid.UUID | None = None
    source: str = Field(default="chatbot1", max_length=64)


class AssistantPrebookIn(BaseModel):
    tenant_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    session_id: str | None = Field(default=None, max_length=255)
    trace_id: str | None = Field(default=None, max_length=255)
    idempotency_key: str = Field(min_length=8, max_length=255)
    customer: AssistantCustomerIn
    booking: AssistantBookingIn
    meta: AssistantMetaIn = Field(default_factory=AssistantMetaIn)


class AssistantPrebookDataOut(BaseModel):
    prebooking_id: str
    appointment_id: str
    customer_id: str
    service_id: str
    location_id: str
    starts_at: datetime
    ends_at: datetime
    needs_confirmation: bool


class AssistantPrebookOut(BaseModel):
    ok: bool
    reference: str
    status: Literal["created", "existing"]
    message: str
    trace_id: str
    data: AssistantPrebookDataOut


def _ref_for(prebooking_id: uuid.UUID) -> str:
    return f"PB-{str(prebooking_id).split('-')[0].upper()}"


def _resolve_actor_id(session, *, tenant_uuid: uuid.UUID, meta: AssistantMetaIn, auth_ctx: dict) -> uuid.UUID | None:
    if auth_ctx.get("mode") == "user":
        try:
            user_uuid = uuid.UUID(str(auth_ctx.get("user_id")))
        except (TypeError, ValueError):
            return None
        if meta.actor_id is not None and meta.actor_id != user_uuid:
            raise ValidationError("actor_mismatch", meta={"actor_id": str(meta.actor_id), "auth_user_id": str(user_uuid)})
        return user_uuid

    if meta.actor_type != "staff" or meta.actor_id is None:
        return None

    stmt = select(UserORM.id).where(UserORM.tenant_id == tenant_uuid).where(UserORM.id == meta.actor_id)
    if session.execute(stmt).scalar_one_or_none() is None:
        raise ValidationError("actor_not_found", meta={"actor_id": str(meta.actor_id)})
    return meta.actor_id


def _resolve_customer(session, request: Request, *, tenant_uuid: uuid.UUID, payload: AssistantCustomerIn) -> uuid.UUID:
    if payload.customer_id is not None:
        stmt = (
            select(CustomerORM.id)
            .where(CustomerORM.tenant_id == tenant_uuid)
            .where(CustomerORM.id == payload.customer_id)
            .where(CustomerORM.deleted_at.is_(None))
        )
        if session.execute(stmt).scalar_one_or_none() is None:
            raise ValidationError("customer_not_found", meta={"customer_id": str(payload.customer_id)})
        return payload.customer_id

    name = (payload.name or "").strip()
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


def _resolve_service(session, *, tenant_uuid: uuid.UUID, service_id: uuid.UUID) -> ServiceORM:
    stmt = (
        select(ServiceORM)
        .where(ServiceORM.tenant_id == tenant_uuid)
        .where(ServiceORM.id == service_id)
        .where(ServiceORM.deleted_at.is_(None))
        .where(ServiceORM.is_active.is_(True))
    )
    svc = session.execute(stmt).scalar_one_or_none()
    if svc is None:
        raise ValidationError("service_not_found_or_inactive", meta={"service_id": str(service_id)})
    return svc


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


@router.post("/assistant/prebook", response_model=AssistantPrebookOut)
def prebook(
    payload: AssistantPrebookIn,
    request: Request,
    x_trace_id: str | None = Header(default=None, alias="X-Trace-Id"),
    _tenant=Depends(require_tenant_header),
    auth_ctx=Depends(require_user_or_assistant_connector),
):
    tenant_id = require_tenant_id()
    if str(payload.tenant_id) != tenant_id:
        raise ValidationError("tenant_mismatch", meta={"header": tenant_id, "body": str(payload.tenant_id)})

    effective_trace_id = payload.trace_id or x_trace_id or str(uuid.uuid4())

    with db_session() as session:
        # Hard tenant validation (middleware currently only sets context).
        container = request.app.state.container
        _ = container.tenant_service.get_or_fail(tenant_id)

        tenant_uuid = uuid.UUID(tenant_id)

        actor_id = _resolve_actor_id(session, tenant_uuid=tenant_uuid, meta=payload.meta, auth_ctx=auth_ctx)

        prebook_repo = AssistantPrebookRequestRepo(session)
        started, existing = prebook_repo.create_started(
            tenant_id=tenant_uuid,
            idempotency_key=payload.idempotency_key,
            conversation_id=payload.conversation_id,
            session_id=payload.session_id,
            trace_id=effective_trace_id,
            actor_type=payload.meta.actor_type,
            actor_id=actor_id,
        )

        if existing is not None:
            if existing.appointment_id is None:
                raise ConflictError(
                    "idempotency_in_progress",
                    meta={"idempotency_key": payload.idempotency_key, "status": existing.status},
                )
            existing_trace_id = existing.trace_id or effective_trace_id
            return AssistantPrebookOut(
                ok=True,
                reference=_ref_for(existing.appointment_id),
                status="existing",
                message="Prebooking already created for this idempotency key.",
                trace_id=existing_trace_id,
                data=AssistantPrebookDataOut(
                    prebooking_id=str(existing.appointment_id),
                    appointment_id=str(existing.appointment_id),
                    customer_id=str(existing.customer_id) if existing.customer_id else "",
                    service_id=str(existing.service_id) if existing.service_id else "",
                    location_id=str(existing.location_id) if existing.location_id else "",
                    starts_at=existing.starts_at,
                    ends_at=existing.ends_at,
                    needs_confirmation=True,
                ),
            )

        assert started is not None

        try:
            customer_id = _resolve_customer(session, request, tenant_uuid=tenant_uuid, payload=payload.customer)
            service = _resolve_service(session, tenant_uuid=tenant_uuid, service_id=payload.booking.service_id)
            location = _resolve_location(
                session,
                tenant_id=tenant_id,
                tenant_uuid=tenant_uuid,
                location_id=payload.booking.location_id,
            )
            starts_utc, ends_utc = _resolve_window(booking=payload.booking, service=service, location=location)

            repo = AppointmentsRepo(session)
            appointment = repo.create(
                tenant_uuid,
                AppointmentCreate(
                    customer_id=customer_id,
                    location_id=location.id,
                    service_id=service.id,
                    starts_at=starts_utc,
                    ends_at=ends_utc,
                    status="booked",
                    needs_confirmation=True,
                    notes=payload.booking.notes or "created via assistant",
                    created_by_user_id=actor_id,
                    updated_by_user_id=actor_id,
                ),
            )

            prebook_repo.mark_created(
                row=started,
                appointment_id=appointment.id,
                customer_id=customer_id,
                service_id=service.id,
                location_id=location.id,
                starts_at=starts_utc,
                ends_at=ends_utc,
            )

            # Best-effort: align assistant conversation session with resolved customer and session_id.
            if payload.conversation_id is not None:
                cs_repo = ChatbotSessionRepo(session)
                entity = cs_repo.get_by_conversation_id(conversation_id=str(payload.conversation_id))
                if entity is not None and entity.tenant_id == tenant_uuid:
                    cs_repo.get_or_create(
                        tenant_id=tenant_id,
                        user_id=str(entity.user_id),
                        client_id=entity.client_id,
                        surface=entity.surface,
                        conversation_id=str(entity.conversation_id),
                        customer_id=str(customer_id),
                    )
                    cs_repo.mark_message(entity=entity, chatbot_session_id=payload.session_id, status="active", error=None)

            return AssistantPrebookOut(
                ok=True,
                reference=_ref_for(appointment.id),
                status="created",
                message="Prebooking created successfully.",
                trace_id=effective_trace_id,
                data=AssistantPrebookDataOut(
                    prebooking_id=str(appointment.id),
                    appointment_id=str(appointment.id),
                    customer_id=str(customer_id),
                    service_id=str(service.id),
                    location_id=str(location.id),
                    starts_at=starts_utc,
                    ends_at=ends_utc,
                    needs_confirmation=bool(getattr(appointment, "needs_confirmation", True)),
                ),
            )

        except AppointmentOverlapError as err:
            prebook_repo.delete(row=started)
            return JSONResponse(status_code=409, content={"error": "APPOINTMENT_OVERLAP", "conflicts": err.conflicts})
        except (ValidationError, NotFoundError) as err:
            prebook_repo.delete(row=started)
            raise err
        except HTTPException:
            prebook_repo.delete(row=started)
            raise
