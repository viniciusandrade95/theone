import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from app.http.deps import require_assistant_token, require_tenant_header
from app.http.routes.assistant_prebook_schemas import PrebookIn
from core.db.session import db_session
from core.errors import ForbiddenError, ValidationError
from core.tenancy import require_tenant_id

from modules.assistant.repo.prebook_request_repo import AssistantPrebookRequestRepo
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.pipeline import PipelineStage
from modules.crm.models.service_orm import ServiceORM
from modules.crm.repo_appointments import AppointmentCreate, AppointmentOverlapError, AppointmentsRepo
from modules.crm.repo_locations import LocationsRepo
from modules.tenants.repo.settings_sql import SqlTenantSettingsRepo


router = APIRouter()

DEFAULT_ASSISTANT_APPOINTMENT_NOTES = "criado pelo assistant"
SUCCESS_MESSAGE = "Pré-reserva criada com sucesso."
_MAX_NOTES_LEN = 1000


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


def _resolve_customer(session, request: Request, *, tenant_uuid: uuid.UUID, payload) -> uuid.UUID:
    if payload.customer_id is not None and str(payload.customer_id).strip():
        try:
            customer_uuid = uuid.UUID(str(payload.customer_id))
        except ValueError:
            raise ValidationError("invalid_customer_id", meta={"customer_id": str(payload.customer_id)})
        stmt = (
            select(CustomerORM.id)
            .where(CustomerORM.tenant_id == tenant_uuid)
            .where(CustomerORM.id == customer_uuid)
            .where(CustomerORM.deleted_at.is_(None))
        )
        if session.execute(stmt).scalar_one_or_none() is None:
            raise ValidationError("customer_not_found", meta={"customer_id": str(payload.customer_id)})
        return customer_uuid

    phone = (payload.phone or "").strip()
    email = str(payload.email).strip().lower() if getattr(payload, "email", None) else None

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

    container = request.app.state.container
    created = container.crm.create_customer(
        name=name,
        phone=phone or None,
        email=email,
        stage=PipelineStage.BOOKED,
    )
    try:
        return uuid.UUID(created.id)
    except ValueError:
        raise ValidationError("invalid_customer_id_created")


def _resolve_service(session, *, tenant_uuid: uuid.UUID, service_id: str) -> ServiceORM:
    raw = (service_id or "").strip()
    if not raw:
        raise ValidationError("missing_service_id")
    try:
        service_uuid = uuid.UUID(raw)
    except ValueError:
        # Fallback by name (case-insensitive).
        desired_key = raw.lower()
        stmt = (
            select(ServiceORM)
            .where(ServiceORM.tenant_id == tenant_uuid)
            .where(ServiceORM.deleted_at.is_(None))
            .where(ServiceORM.is_active.is_(True))
            .where(func.lower(ServiceORM.name) == desired_key)
        )
        matches = list(session.execute(stmt).scalars().all())
        if not matches:
            raise ValidationError("service_not_found", meta={"service_name": raw})
        if len(matches) > 1:
            raise ValidationError("service_ambiguous", meta={"service_name": raw, "count": len(matches)})
        return matches[0]

    AppointmentsRepo(session)._assert_service_is_usable(
        tenant_id=tenant_uuid,
        service_id=service_uuid,
        require_active=True,
    )
    stmt = (
        select(ServiceORM)
        .where(ServiceORM.tenant_id == tenant_uuid)
        .where(ServiceORM.id == service_uuid)
        .where(ServiceORM.deleted_at.is_(None))
    )
    svc = session.execute(stmt).scalar_one_or_none()
    if svc is None:
        raise ValidationError("service_not_found_or_inactive", meta={"service_id": raw})
    return svc


def _resolve_location(session, *, tenant_id: str, tenant_uuid: uuid.UUID, location_id: str | None) -> LocationORM:
    if not (location_id or "").strip():
        return _resolve_default_location(session, tenant_id=tenant_id)
    try:
        location_uuid = uuid.UUID(location_id)
    except ValueError:
        raise ValidationError("invalid_location_id", meta={"location_id": location_id})
    stmt = (
        select(LocationORM)
        .where(LocationORM.tenant_id == tenant_uuid)
        .where(LocationORM.id == location_uuid)
        .where(LocationORM.deleted_at.is_(None))
        .where(LocationORM.is_active.is_(True))
    )
    loc = session.execute(stmt).scalar_one_or_none()
    if loc is None:
        raise ValidationError("location_not_found", meta={"location_id": str(location_id)})
    return loc


def _parse_requested_date_time(*, requested_date: str, requested_time: str) -> tuple[date, time]:
    try:
        parsed_date = date.fromisoformat(requested_date)
    except ValueError:
        raise ValidationError("invalid_requested_date", meta={"requested_date": requested_date})
    try:
        parsed_time = time.fromisoformat(requested_time)
    except ValueError:
        raise ValidationError("invalid_requested_time", meta={"requested_time": requested_time})
    return parsed_date, parsed_time


def _resolve_window(*, booking, service: ServiceORM, location: LocationORM) -> tuple[datetime, datetime]:
    duration_min = int(service.duration_minutes)

    if booking.starts_at is not None:
        if booking.starts_at.tzinfo is None:
            raise ValidationError("starts_at_must_be_timezone_aware")
        starts_utc = booking.starts_at.astimezone(timezone.utc)
    else:
        tz_name = (booking.timezone or "").strip() if getattr(booking, "timezone", None) else ""
        tz_name = tz_name or location.timezone
        tz = _ensure_tz(tz_name)
        requested_date, requested_time = _parse_requested_date_time(
            requested_date=booking.requested_date,
            requested_time=booking.requested_time,
        )
        local = datetime.combine(requested_date, requested_time, tzinfo=tz)
        starts_utc = local.astimezone(timezone.utc)

    if booking.ends_at is not None:
        if booking.ends_at.tzinfo is None:
            raise ValidationError("ends_at_must_be_timezone_aware")
        ends_utc = booking.ends_at.astimezone(timezone.utc)
    else:
        ends_utc = starts_utc + timedelta(minutes=duration_min)

    return starts_utc, ends_utc


def _compose_notes(user_notes: str | None) -> str:
    base = DEFAULT_ASSISTANT_APPOINTMENT_NOTES
    extra = (user_notes or "").strip()
    if not extra:
        return base
    merged = f"{base} | {extra}"
    if len(merged) <= _MAX_NOTES_LEN:
        return merged
    # Truncate user notes to fit.
    allowed = max(0, _MAX_NOTES_LEN - len(base) - len(" | "))
    return f"{base} | {extra[:allowed]}".rstrip()


@router.post("/assistant/prebook", status_code=201)
def prebook(
    payload: PrebookIn,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _tenant=Depends(require_tenant_header),
    _auth=Depends(require_assistant_token),
):
    tenant_id = require_tenant_id()
    if payload.tenant_id is not None and str(payload.tenant_id) != tenant_id:
        raise ForbiddenError("tenant_mismatch", meta={"header": tenant_id, "body": str(payload.tenant_id)})

    effective_idem = (idempotency_key or payload.idempotency_key or "").strip() or None

    with db_session() as session:
        container = request.app.state.container
        container.tenant_service.get_or_fail(tenant_id)

        tenant_uuid = uuid.UUID(tenant_id)

        prebook_repo = AssistantPrebookRequestRepo(session)
        started = None
        if effective_idem is not None:
            started, existing = prebook_repo.create_started(
                tenant_id=tenant_uuid,
                idempotency_key=effective_idem,
                conversation_id=None,
                session_id=payload.session_id,
                trace_id=payload.trace_id,
                actor_type=None,
                actor_id=None,
            )
            if existing is not None:
                if existing.appointment_id is not None:
                    appointment_id = str(existing.appointment_id)
                    return {"ok": True, "prebooking_id": appointment_id, "reference": appointment_id, "message": SUCCESS_MESSAGE}
                return JSONResponse(
                    status_code=409,
                    content={"message": "Horário indisponível", "error_code": "conflict", "retriable": False},
                )

        try:
            customer_id = _resolve_customer(session, request, tenant_uuid=tenant_uuid, payload=payload.customer)
            location = _resolve_location(
                session,
                tenant_id=tenant_id,
                tenant_uuid=tenant_uuid,
                location_id=payload.booking.location_id,
            )
            service = _resolve_service(session, tenant_uuid=tenant_uuid, service_id=payload.booking.service_id)
            starts_utc, ends_utc = _resolve_window(booking=payload.booking, service=service, location=location)
            if ends_utc <= starts_utc:
                return JSONResponse(status_code=400, content={"message": "ends_at must be after starts_at"})

            # Best-effort idempotency: reuse if same customer+location+service+starts_at already exists (and not cancelled).
            reuse_stmt = (
                select(AppointmentORM.id)
                .where(AppointmentORM.tenant_id == tenant_uuid)
                .where(AppointmentORM.customer_id == customer_id)
                .where(AppointmentORM.location_id == location.id)
                .where(AppointmentORM.service_id == service.id)
                .where(AppointmentORM.starts_at == starts_utc)
                .where(AppointmentORM.deleted_at.is_(None))
                .where(AppointmentORM.status != "cancelled")
            )
            reused_id = session.execute(reuse_stmt).scalar_one_or_none()
            if reused_id is not None:
                appointment_id = str(reused_id)
                if started is not None:
                    prebook_repo.mark_created(
                        row=started,
                        appointment_id=reused_id,
                        customer_id=customer_id,
                        service_id=service.id,
                        location_id=location.id,
                        starts_at=starts_utc,
                        ends_at=ends_utc,
                    )
                return JSONResponse(
                    status_code=200,
                    content={"ok": True, "prebooking_id": appointment_id, "reference": appointment_id, "message": SUCCESS_MESSAGE},
                )

            repo = AppointmentsRepo(session)
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
                    notes=_compose_notes(payload.booking.notes),
                    created_by_user_id=None,
                    updated_by_user_id=None,
                ),
            )

            if started is not None:
                prebook_repo.mark_created(
                    row=started,
                    appointment_id=appointment.id,
                    customer_id=customer_id,
                    service_id=service.id,
                    location_id=location.id,
                    starts_at=starts_utc,
                    ends_at=ends_utc,
                )

            appointment_id = str(appointment.id)
            return {"ok": True, "prebooking_id": appointment_id, "reference": appointment_id, "message": SUCCESS_MESSAGE}
        except AppointmentOverlapError:
            if started is not None:
                prebook_repo.delete(row=started)
            return JSONResponse(
                status_code=409,
                content={"message": "Horário indisponível", "error_code": "conflict", "retriable": False},
            )
        except ValidationError as err:
            if started is not None:
                prebook_repo.delete(row=started)
            if err.message in {
                "missing_service_id",
                "invalid_service_id",
                "service_not_found",
                "service_ambiguous",
                "service_not_found_or_inactive",
            }:
                return JSONResponse(
                    status_code=400,
                    content={"error": "VALIDATION_ERROR", "details": {"message": err.message, **(err.meta or {})}},
                )
            return JSONResponse(
                status_code=422,
                content={"error": "VALIDATION_ERROR", "details": {"message": err.message, **(err.meta or {})}},
            )
        except Exception:
            if started is not None:
                prebook_repo.delete(row=started)
            raise
