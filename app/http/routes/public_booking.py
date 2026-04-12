import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from core.db.session import db_session
from core.tenancy import clear_tenant_id, set_tenant_id
from core.errors import ValidationError
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.crm.models.pipeline import PipelineStage
from modules.crm.repo_appointments import AppointmentOverlapError, AppointmentsRepo, AppointmentCreate
from modules.crm.repo_locations import LocationsRepo
from modules.tenants.models.tenant_settings_orm import TenantSettingsORM
from modules.tenants.repo.booking_settings_sql import SqlBookingSettingsRepo


router = APIRouter()


def _not_found(message: str):
    return JSONResponse(status_code=404, content={"error": "NOT_FOUND", "details": {"message": message}})


def _bad_request(message: str, *, fields: dict | None = None):
    details: dict[str, object] = {"message": message}
    if fields:
        details["fields"] = fields
    return JSONResponse(status_code=400, content={"error": "VALIDATION_ERROR", "details": details})


@contextmanager
def _public_tenant(tenant_id: str):
    clear_tenant_id()
    set_tenant_id(tenant_id)
    try:
        yield
    finally:
        clear_tenant_id()


def _ensure_tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _weekday_key(d: date) -> str:
    keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    return keys[d.weekday()]


@dataclass(frozen=True)
class _HoursWindow:
    opens_at: time
    closes_at: time


def _parse_hhmm(value: str) -> time | None:
    raw = (value or "").strip()
    if len(raw) != 5 or raw[2] != ":":
        return None
    try:
        hh = int(raw[0:2])
        mm = int(raw[3:5])
    except ValueError:
        return None
    if hh < 0 or hh > 23 or mm < 0 or mm > 59:
        return None
    return time(hour=hh, minute=mm)


def _hours_for_location(location: LocationORM, for_date: date) -> _HoursWindow | None:
    hours = location.hours_json or None
    if isinstance(hours, dict):
        day = hours.get(_weekday_key(for_date))
        if isinstance(day, dict):
            open_raw = day.get("open")
            close_raw = day.get("close")
            if isinstance(open_raw, str) and isinstance(close_raw, str):
                opens_at = _parse_hhmm(open_raw)
                closes_at = _parse_hhmm(close_raw)
                if opens_at and closes_at and opens_at < closes_at:
                    return _HoursWindow(opens_at=opens_at, closes_at=closes_at)
            return None
        # hours_json existe mas não tem o dia: consideramos fechado
        return None

    # fallback simples (apenas se não houver hours_json)
    return _HoursWindow(opens_at=time(9, 0), closes_at=time(17, 0))


def _ceil_dt(dt: datetime, *, step_minutes: int) -> datetime:
    step = timedelta(minutes=step_minutes)
    epoch = datetime(1970, 1, 1, tzinfo=dt.tzinfo)
    delta = dt - epoch
    remainder = delta % step
    if remainder == timedelta(0):
        return dt
    return dt + (step - remainder)


class PublicServiceOut(BaseModel):
    id: str
    name: str
    duration_minutes: int
    price_cents: int | None


class PublicLocationOut(BaseModel):
    id: str
    name: str
    timezone: str


class PublicBookingConfigOut(BaseModel):
    slug: str
    business_name: str
    contact_phone: str | None
    contact_email: str | None
    primary_color: str | None
    logo_url: str | None
    services: list[PublicServiceOut]
    locations: list[PublicLocationOut]
    requires_location: bool


class AvailabilitySlotOut(BaseModel):
    starts_at: datetime
    ends_at: datetime
    label: str


class AvailabilityOut(BaseModel):
    date: str
    timezone: str
    slots: list[AvailabilitySlotOut]


class CreatePublicAppointmentIn(BaseModel):
    service_id: str
    starts_at: datetime
    location_id: str | None = None
    customer_name: str = Field(min_length=1, max_length=255)
    customer_phone: str = Field(min_length=1, max_length=40)
    customer_email: EmailStr | None = None
    note: str | None = Field(default=None, max_length=1000)


class CreatePublicAppointmentOut(BaseModel):
    ok: bool
    appointment_id: str
    needs_confirmation: bool


def _get_public_settings_or_404(slug: str):
    with db_session() as session:
        repo = SqlBookingSettingsRepo(session)
        settings = repo.get_by_slug(slug=slug)
        if settings is None:
            return None, _not_found("Link de marcação não encontrado.")
        if not settings.booking_enabled:
            return None, _not_found("Este link de marcação não está ativo.")
        # Ensure settings is safe to use outside this DB session.
        # `db_session()` commits and expires instances by default; without expunging, routes
        # may hit DetachedInstanceError when reading attributes after the context closes.
        session.expunge(settings)
        return settings, None


def _list_active_locations(session, tenant_id: str) -> list[LocationORM]:
    repo = LocationsRepo(session)
    return repo.list_locations(tenant_id=tenant_id, include_inactive=False, include_deleted=False)


def _resolve_location(session, tenant_id: str, location_id: str | None) -> tuple[LocationORM | None, JSONResponse | None]:
    locations = _list_active_locations(session, tenant_id)
    if not locations:
        return None, _bad_request("Este negócio não tem localizações disponíveis.")
    if len(locations) == 1 and not location_id:
        return locations[0], None
    if not location_id:
        return None, _bad_request("Seleciona uma localização.")
    try:
        loc_uuid = uuid.UUID(location_id)
    except ValueError:
        return None, _bad_request("Localização inválida.")
    candidate = next((l for l in locations if l.id == loc_uuid), None)
    if candidate is None:
        return None, _bad_request("Localização inválida.")
    return candidate, None


def _resolve_service(session, tenant_id: str, service_id: str) -> tuple[ServiceORM | None, JSONResponse | None]:
    try:
        svc_uuid = uuid.UUID(service_id)
    except ValueError:
        return None, _bad_request("Serviço inválido.")
    stmt = (
        select(ServiceORM)
        .where(ServiceORM.tenant_id == uuid.UUID(tenant_id))
        .where(ServiceORM.id == svc_uuid)
        .where(ServiceORM.deleted_at.is_(None))
    )
    svc = session.execute(stmt).scalar_one_or_none()
    if svc is None:
        return None, _bad_request("Serviço inválido.")
    if not svc.is_active:
        return None, _bad_request("Este serviço não está disponível.")
    if not getattr(svc, "is_bookable_online", False):
        return None, _bad_request("Este serviço não está disponível para marcação online.")
    return svc, None


def _validate_notice_window(settings, tz: ZoneInfo, starts_at_local: datetime, *, duration_minutes: int) -> JSONResponse | None:
    now_local = datetime.now(timezone.utc).astimezone(tz)
    earliest = now_local + timedelta(minutes=int(settings.min_booking_notice_minutes))
    latest = now_local + timedelta(days=int(settings.max_booking_notice_days))
    if starts_at_local < earliest:
        return _bad_request("Escolhe um horário com mais antecedência.")
    if starts_at_local + timedelta(minutes=duration_minutes) > latest:
        return _bad_request("Este horário está fora da janela máxima de marcação.")
    return None


def _busy_intervals(session, tenant_id: str, location_id: uuid.UUID, from_utc: datetime, to_utc: datetime) -> list[tuple[datetime, datetime]]:
    stmt = (
        select(AppointmentORM.starts_at, AppointmentORM.ends_at, AppointmentORM.status)
        .where(AppointmentORM.tenant_id == uuid.UUID(tenant_id))
        .where(AppointmentORM.location_id == location_id)
        .where(AppointmentORM.deleted_at.is_(None))
        .where(AppointmentORM.starts_at < to_utc)
        .where(AppointmentORM.ends_at > from_utc)
    )
    rows = session.execute(stmt).all()
    intervals: list[tuple[datetime, datetime]] = []
    for starts_at, ends_at, status in rows:
        if str(status) == "cancelled":
            continue
        if starts_at is None or ends_at is None:
            continue
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        intervals.append((starts_at, ends_at))
    return intervals


def _interval_free(candidate_start_utc: datetime, candidate_end_utc: datetime, busy: list[tuple[datetime, datetime]]) -> bool:
    for s, e in busy:
        if s < candidate_end_utc and e > candidate_start_utc:
            return False
    return True


@router.get("/public/book/{slug}", response_model=PublicBookingConfigOut)
def public_booking_config(slug: str):
    settings, err = _get_public_settings_or_404(slug)
    if err:
        return err

    tenant_id = str(settings.tenant_id)
    with _public_tenant(tenant_id):
        with db_session() as session:
            # branding opcional via tenant_settings (reuso)
            tenant_settings = session.get(TenantSettingsORM, uuid.UUID(tenant_id))
            primary_color = tenant_settings.primary_color if tenant_settings else None
            logo_url = tenant_settings.logo_url if tenant_settings else None

            stmt = (
                select(ServiceORM)
                .where(ServiceORM.tenant_id == uuid.UUID(tenant_id))
                .where(ServiceORM.deleted_at.is_(None))
                .where(ServiceORM.is_active.is_(True))
                .where(ServiceORM.is_bookable_online.is_(True))
                .order_by(ServiceORM.name.asc())
            )
            services = session.execute(stmt).scalars().all()

            locations = _list_active_locations(session, tenant_id)
            return PublicBookingConfigOut(
                slug=str(settings.booking_slug),
                business_name=settings.public_business_name or "",
                contact_phone=settings.public_contact_phone,
                contact_email=settings.public_contact_email,
                primary_color=primary_color,
                logo_url=logo_url,
                services=[
                    PublicServiceOut(
                        id=str(s.id),
                        name=s.name,
                        duration_minutes=int(s.duration_minutes),
                        price_cents=int(s.price_cents) if s.price_cents is not None else None,
                    )
                    for s in services
                ],
                locations=[PublicLocationOut(id=str(l.id), name=l.name, timezone=l.timezone) for l in locations],
                requires_location=len(locations) > 1,
            )


@router.get("/public/book/{slug}/availability", response_model=AvailabilityOut)
def public_booking_availability(
    slug: str,
    service_id: str = Query(...),
    date_str: str = Query(..., alias="date"),
    location_id: str | None = Query(default=None),
):
    settings, err = _get_public_settings_or_404(slug)
    if err:
        return err

    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return _bad_request("Data inválida.", fields={"date": "Invalid date"})

    tenant_id = str(settings.tenant_id)
    with _public_tenant(tenant_id):
        with db_session() as session:
            service, svc_err = _resolve_service(session, tenant_id, service_id)
            if svc_err:
                return svc_err

            location, loc_err = _resolve_location(session, tenant_id, location_id)
            if loc_err:
                return loc_err

            assert service is not None
            assert location is not None

            tz = _ensure_tz(location.timezone)
            hours = _hours_for_location(location, target_date)
            if hours is None:
                return AvailabilityOut(date=target_date.isoformat(), timezone=str(tz), slots=[])

            start_local = datetime.combine(target_date, hours.opens_at, tzinfo=tz)
            end_local = datetime.combine(target_date, hours.closes_at, tzinfo=tz)
            from_utc = start_local.astimezone(timezone.utc)
            to_utc = end_local.astimezone(timezone.utc)

            busy = _busy_intervals(session, tenant_id, location.id, from_utc, to_utc)
            duration = int(service.duration_minutes)
            step_minutes = 15

            now_local = datetime.now(timezone.utc).astimezone(tz)
            earliest = _ceil_dt(now_local + timedelta(minutes=int(settings.min_booking_notice_minutes)), step_minutes=step_minutes)
            latest = now_local + timedelta(days=int(settings.max_booking_notice_days))

            cursor = _ceil_dt(start_local, step_minutes=step_minutes)
            slots: list[AvailabilitySlotOut] = []
            while cursor + timedelta(minutes=duration) <= end_local:
                # notice window
                if cursor >= earliest and cursor + timedelta(minutes=duration) <= latest:
                    candidate_start_utc = cursor.astimezone(timezone.utc)
                    candidate_end_utc = (cursor + timedelta(minutes=duration)).astimezone(timezone.utc)
                    if _interval_free(candidate_start_utc, candidate_end_utc, busy):
                        slots.append(
                            AvailabilitySlotOut(
                                starts_at=candidate_start_utc,
                                ends_at=candidate_end_utc,
                                label=cursor.strftime("%H:%M"),
                            )
                        )
                cursor = cursor + timedelta(minutes=step_minutes)

            return AvailabilityOut(date=target_date.isoformat(), timezone=str(tz), slots=slots)


@router.post("/public/book/{slug}/appointments", response_model=CreatePublicAppointmentOut)
def public_create_booking(slug: str, payload: CreatePublicAppointmentIn, request: Request):
    settings, err = _get_public_settings_or_404(slug)
    if err:
        return err

    tenant_id = str(settings.tenant_id)
    with _public_tenant(tenant_id):
        with db_session() as session:
            service, svc_err = _resolve_service(session, tenant_id, payload.service_id)
            if svc_err:
                return svc_err

            location, loc_err = _resolve_location(session, tenant_id, payload.location_id)
            if loc_err:
                return loc_err

            assert service is not None
            assert location is not None

            tz = _ensure_tz(location.timezone)
            starts_at_local = payload.starts_at
            if starts_at_local.tzinfo is None:
                starts_at_local = starts_at_local.replace(tzinfo=tz)
            else:
                starts_at_local = starts_at_local.astimezone(tz)

            duration = int(service.duration_minutes)
            ends_at_local = starts_at_local + timedelta(minutes=duration)

            hours = _hours_for_location(location, starts_at_local.date())
            if hours is None:
                return _bad_request("Este horário está fora do horário de funcionamento.")
            open_local = datetime.combine(starts_at_local.date(), hours.opens_at, tzinfo=tz)
            close_local = datetime.combine(starts_at_local.date(), hours.closes_at, tzinfo=tz)
            if starts_at_local < open_local or ends_at_local > close_local:
                return _bad_request("Este horário está fora do horário de funcionamento.")

            notice_err = _validate_notice_window(settings, tz, starts_at_local, duration_minutes=duration)
            if notice_err:
                return notice_err

            customer_name = payload.customer_name.strip()
            phone = payload.customer_phone.strip()
            email = str(payload.customer_email).strip().lower() if payload.customer_email else None

            # lookup conservador: telefone -> email, com detecção de conflitos
            customer_by_phone = None
            if phone:
                stmt = (
                    select(CustomerORM)
                    .where(CustomerORM.tenant_id == uuid.UUID(tenant_id))
                    .where(CustomerORM.phone == phone)
                    .where(CustomerORM.deleted_at.is_(None))
                )
                customer_by_phone = session.execute(stmt).scalar_one_or_none()

            customer_by_email = None
            if email:
                stmt = (
                    select(CustomerORM)
                    .where(CustomerORM.tenant_id == uuid.UUID(tenant_id))
                    .where(CustomerORM.email == email)
                    .where(CustomerORM.deleted_at.is_(None))
                )
                customer_by_email = session.execute(stmt).scalar_one_or_none()

            if customer_by_phone and customer_by_email and customer_by_phone.id != customer_by_email.id:
                return _bad_request("O telefone e o email indicam clientes diferentes. Confirma os dados.")

            customer = customer_by_phone or customer_by_email
            if customer is None:
                container = request.app.state.container
                created = container.crm.create_customer(
                    name=customer_name,
                    phone=phone,
                    email=email,
                    stage=PipelineStage.BOOKED,
                )
                customer_id = uuid.UUID(created.id)
            else:
                customer_id = customer.id

            starts_at_utc = starts_at_local.astimezone(timezone.utc)
            ends_at_utc = ends_at_local.astimezone(timezone.utc)

            # impede duplicação óbvia (mesmo customer, mesmo slot)
            dup_stmt = (
                select(AppointmentORM.id)
                .where(AppointmentORM.tenant_id == uuid.UUID(tenant_id))
                .where(AppointmentORM.customer_id == customer_id)
                .where(AppointmentORM.location_id == location.id)
                .where(AppointmentORM.starts_at == starts_at_utc)
                .where(AppointmentORM.deleted_at.is_(None))
                .where(AppointmentORM.status != "cancelled")
            )
            if session.execute(dup_stmt).scalar_one_or_none() is not None:
                return _bad_request("Já existe uma marcação para este horário.")

            repo = AppointmentsRepo(session)
            try:
                appointment = repo.create(
                    uuid.UUID(tenant_id),
                    AppointmentCreate(
                        customer_id=customer_id,
                        location_id=location.id,
                        service_id=service.id,
                        starts_at=starts_at_utc,
                        ends_at=ends_at_utc,
                        status="booked",
                        needs_confirmation=not bool(settings.auto_confirm_bookings),
                        notes=payload.note,
                        created_by_user_id=None,
                        updated_by_user_id=None,
                    ),
                )
            except AppointmentOverlapError:
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": "CONFLICT",
                        "details": {"message": "Este horário já não está disponível. Por favor escolhe outro."},
                    },
                )
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=e.message)

            return CreatePublicAppointmentOut(
                ok=True,
                appointment_id=str(appointment.id),
                needs_confirmation=bool(getattr(appointment, "needs_confirmation", False)),
            )
