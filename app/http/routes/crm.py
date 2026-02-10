import uuid
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

from core.errors import NotFoundError, ValidationError
from app.http.deps import require_tenant_header, require_user
from modules.crm.models import PipelineStage

from core.tenancy import require_tenant_id
from core.db.session import db_session

from modules.crm.api.contracts import (
    LocationCreate,
    LocationDefaultOut,
    LocationListOut,
    LocationOut,
    LocationUpdate,
)
from modules.crm.repo_locations import LocationCreateData, LocationsRepo
from modules.crm.repo_services import ServicesRepo, ServiceCreate
from modules.crm.repo_appointments import AppointmentOverlapError, AppointmentsRepo, AppointmentCreate
from modules.tenants.repo.settings_sql import SqlTenantSettingsRepo

router = APIRouter()


class CreateCustomerIn(BaseModel):
    name: str
    phone: str | None = None
    email: EmailStr | None = None
    tags: list[str] = []
    consent_marketing: bool = False
    consent_marketing_at: datetime | None = None
    stage: PipelineStage = PipelineStage.LEAD


class UpdateCustomerIn(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    tags: list[str] | None = None
    consent_marketing: bool | None = None
    stage: PipelineStage | None = None


class AddInteractionIn(BaseModel):
    type: str
    content: str


class MoveStageIn(BaseModel):
    to_stage: PipelineStage


class CustomerListOut(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


class InteractionOut(BaseModel):
    id: str
    type: str
    content: str
    created_at: datetime


class InteractionListOut(BaseModel):
    items: list[InteractionOut]
    total: int
    page: int
    page_size: int


class TenantSettingsUpdateIn(BaseModel):
    business_name: str | None = Field(default=None, max_length=255)
    default_timezone: str | None = Field(default=None, min_length=1, max_length=120)
    currency: str | None = Field(default=None, min_length=1, max_length=12)
    calendar_default_view: Literal["week", "day"] | None = None
    default_location_id: str | None = None
    primary_color: str | None = Field(default=None, max_length=32)
    logo_url: str | None = Field(default=None, max_length=1024)

    @field_validator("default_timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        tz = value.strip()
        try:
            ZoneInfo(tz)
        except ZoneInfoNotFoundError:
            raise ValueError("Invalid IANA timezone")
        return tz


class TenantSettingsOut(BaseModel):
    tenant_id: str
    business_name: str | None
    default_timezone: str
    currency: str
    calendar_default_view: Literal["week", "day"]
    default_location_id: str | None
    primary_color: str | None
    logo_url: str | None
    created_at: datetime
    updated_at: datetime


def _to_location_out(location) -> LocationOut:
    return LocationOut(
        id=str(location.id),
        tenant_id=str(location.tenant_id),
        name=location.name,
        timezone=location.timezone,
        address_line1=location.address_line1,
        address_line2=location.address_line2,
        city=location.city,
        postcode=location.postcode,
        country=location.country,
        phone=location.phone,
        email=location.email,
        is_active=location.is_active,
        hours_json=location.hours_json,
        allow_overlaps=location.allow_overlaps,
        created_at=location.created_at,
        updated_at=location.updated_at,
        deleted_at=location.deleted_at,
    )


def _to_tenant_settings_out(settings) -> TenantSettingsOut:
    calendar_default_view = settings.calendar_default_view if settings.calendar_default_view in {"week", "day"} else "week"
    return TenantSettingsOut(
        tenant_id=str(settings.tenant_id),
        business_name=settings.business_name,
        default_timezone=settings.default_timezone,
        currency=settings.currency,
        calendar_default_view=calendar_default_view,
        default_location_id=str(settings.default_location_id) if settings.default_location_id else None,
        primary_color=settings.primary_color,
        logo_url=settings.logo_url,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


def _to_customer_out(cust) -> dict:
    return {
        "id": cust.id,
        "name": cust.name,
        "phone": cust.phone,
        "email": cust.email,
        "tags": list(cust.tags),
        "stage": cust.stage.value,
        "consent_marketing": cust.consent_marketing,
        "consent_marketing_at": cust.consent_marketing_at.isoformat() if cust.consent_marketing_at else None,
        "created_at": cust.created_at.isoformat(),
    }


def _resolve_settings_location(session, tenant_id: str):
    settings_repo = SqlTenantSettingsRepo(session)
    locations_repo = LocationsRepo(session)

    settings = settings_repo.get_or_create(tenant_id=tenant_id)

    location = None
    if settings.default_location_id is not None:
        location = locations_repo.get_location(
            tenant_id=tenant_id,
            location_id=str(settings.default_location_id),
        )

    if location is None:
        location = locations_repo.ensure_default_location(tenant_id=tenant_id)
        if settings.default_location_id != location.id:
            settings_repo.update(tenant_id=tenant_id, patch={"default_location_id": str(location.id)})
    return location


@router.post("/customers")
def create_customer(payload: CreateCustomerIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.create_customer(
        name=payload.name,
        phone=payload.phone,
        email=str(payload.email) if payload.email else None,
        tags=set(payload.tags),
        consent_marketing=payload.consent_marketing,
        consent_marketing_at=payload.consent_marketing_at,
        stage=payload.stage,
    )
    return _to_customer_out(cust)


@router.get("/customers", response_model=CustomerListOut)
def list_customers(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    query: str | None = None,
    search: str | None = None,
    stage: PipelineStage | None = None,
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    c = request.app.state.container
    effective_query = query if query is not None else search
    customers = c.crm.list_customers(
        page=page,
        page_size=page_size,
        query=effective_query,
        stage=stage,
        sort=sort,
        order=order,
    )
    total = c.crm.count_customers(query=effective_query, stage=stage)
    return {
        "items": [_to_customer_out(cust) for cust in customers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/customers/{customer_id}")
def get_customer(customer_id: str, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.get_customer(customer_id=customer_id)
    return _to_customer_out(cust)


def _update_customer(
    customer_id: str,
    payload: UpdateCustomerIn,
    request: Request,
):
    c = request.app.state.container
    cust = c.crm.update_customer(
        customer_id=customer_id,
        name=payload.name,
        phone=payload.phone,
        email=str(payload.email) if payload.email else None,
        tags=set(payload.tags) if payload.tags is not None else None,
        consent_marketing=payload.consent_marketing,
        stage=payload.stage,
    )
    return _to_customer_out(cust)


@router.patch("/customers/{customer_id}")
def update_customer_patch(
    customer_id: str,
    payload: UpdateCustomerIn,
    request: Request,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    return _update_customer(customer_id, payload, request)


@router.put("/customers/{customer_id}")
def update_customer_put(
    customer_id: str,
    payload: UpdateCustomerIn,
    request: Request,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    return _update_customer(customer_id, payload, request)


@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: str, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    c.crm.delete_customer(customer_id=customer_id)
    return {"status": "deleted"}


@router.post("/customers/{customer_id}/interactions")
def add_interaction(customer_id: str, payload: AddInteractionIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    i = c.crm.add_interaction(customer_id=customer_id, type=payload.type, content=payload.content)
    return {"id": i.id, "type": i.type, "content": i.content, "created_at": i.created_at.isoformat()}


@router.get("/customers/{customer_id}/interactions", response_model=InteractionListOut)
def list_interactions(
    customer_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    query: str | None = None,
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    c = request.app.state.container
    interactions = c.crm.list_interactions(
        customer_id=customer_id,
        page=page,
        page_size=page_size,
        query=query,
        sort=sort,
        order=order,
    )
    total = c.crm.count_interactions(customer_id=customer_id, query=query)
    return {
        "items": [
            InteractionOut(
                id=i.id,
                type=i.type,
                content=i.content,
                created_at=i.created_at,
            )
            for i in interactions
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/customers/{customer_id}/stage")
def move_stage(customer_id: str, payload: MoveStageIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.move_stage(customer_id=customer_id, to_stage=payload.to_stage)
    return {"id": cust.id, "stage": cust.stage.value}


@router.get("/settings", response_model=TenantSettingsOut)
def get_tenant_settings(_tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = SqlTenantSettingsRepo(session)
        settings = repo.get_or_create(tenant_id=tenant_id)
        return _to_tenant_settings_out(settings)


@router.put("/settings", response_model=TenantSettingsOut)
def update_tenant_settings(
    payload: TenantSettingsUpdateIn,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    patch = payload.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = SqlTenantSettingsRepo(session)
        try:
            settings = repo.update(tenant_id=tenant_id, patch=patch)
        except ValidationError as err:
            raise HTTPException(status_code=400, detail=err.message)
        return _to_tenant_settings_out(settings)


@router.get("/settings/location", response_model=LocationOut)
def get_settings_location(_tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    with db_session() as session:
        location = _resolve_settings_location(session=session, tenant_id=tenant_id)
        return _to_location_out(location)


@router.put("/settings/location", response_model=LocationOut)
def update_settings_location(
    payload: LocationUpdate,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    patch = payload.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    if patch.get("is_active") is False:
        raise HTTPException(status_code=400, detail="Default location cannot be deactivated from settings")

    tenant_id = require_tenant_id()
    with db_session() as session:
        location = _resolve_settings_location(session=session, tenant_id=tenant_id)
        repo = LocationsRepo(session)
        try:
            updated = repo.update_location(
                tenant_id=tenant_id,
                location_id=str(location.id),
                patch=patch,
            )
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=err.message)
        return _to_location_out(updated)


@router.get("/locations", response_model=LocationListOut)
def list_locations(
    include_inactive: bool = Query(default=False),
    include_deleted: bool = Query(default=False),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = LocationsRepo(session)
        items = repo.list_locations(
            tenant_id=tenant_id,
            include_inactive=include_inactive,
            include_deleted=include_deleted,
        )
        return LocationListOut(items=[_to_location_out(location) for location in items])


@router.get("/locations/default", response_model=LocationDefaultOut)
def get_default_location(_tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = LocationsRepo(session)
        location = repo.ensure_default_location(tenant_id)
        settings_repo = SqlTenantSettingsRepo(session)
        settings = settings_repo.get_or_create(tenant_id=tenant_id)
        if settings.default_location_id != location.id:
            settings_repo.update(tenant_id=tenant_id, patch={"default_location_id": str(location.id)})
        return LocationDefaultOut(
            id=str(location.id),
            name=location.name,
            timezone=location.timezone,
            allow_overlaps=location.allow_overlaps,
            hours_json=location.hours_json,
        )


@router.post("/locations", response_model=LocationOut)
def create_location(payload: LocationCreate, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = LocationsRepo(session)
        location = repo.create_location(
            tenant_id=tenant_id,
            payload=LocationCreateData(**payload.model_dump()),
        )
        return _to_location_out(location)


@router.get("/locations/{location_id}", response_model=LocationOut)
def get_location(location_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = LocationsRepo(session)
        location = repo.get_location(tenant_id=tenant_id, location_id=location_id)
        if location is None:
            raise HTTPException(status_code=404, detail="location_not_found")
        return _to_location_out(location)


@router.put("/locations/{location_id}", response_model=LocationOut)
def update_location(
    location_id: str,
    payload: LocationUpdate,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    patch = payload.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = LocationsRepo(session)
        try:
            location = repo.update_location(tenant_id=tenant_id, location_id=location_id, patch=patch)
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=err.message)
        return _to_location_out(location)


@router.delete("/locations/{location_id}")
def delete_location(location_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = require_tenant_id()
    with db_session() as session:
        repo = LocationsRepo(session)
        try:
            repo.delete_location(tenant_id=tenant_id, location_id=location_id)
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=err.message)
    return {"ok": True}



##### service and appointments

class ServiceIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    price_cents: int | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class ServiceOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    price_cents: int
    duration_minutes: int
    is_active: bool


class ServiceListOut(BaseModel):
    items: list[ServiceOut]
    total: int
    page: int
    page_size: int


class AppointmentCreateIn(BaseModel):
    customer_id: str
    location_id: str
    service_id: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: str = "booked"
    notes: str | None = None
    cancelled_reason: str | None = None


class AppointmentUpdateIn(BaseModel):
    customer_id: str | None = None
    location_id: str | None = None
    service_id: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = None
    notes: str | None = None
    cancelled_reason: str | None = None


class AppointmentOut(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    location_id: str
    service_id: str | None
    starts_at: datetime
    ends_at: datetime
    status: str
    cancelled_reason: str | None
    status_updated_at: datetime
    notes: str | None
    created_by_user_id: str | None
    updated_by_user_id: str | None
    created_at: datetime


class AppointmentListOut(BaseModel):
    items: list[AppointmentOut]
    total: int
    page: int
    page_size: int


class CalendarCustomerOut(BaseModel):
    id: str
    name: str
    phone: str | None


class CalendarServiceOut(BaseModel):
    id: str
    name: str
    duration_min: int | None
    price: float | None


class CalendarItemOut(BaseModel):
    id: str
    starts_at: datetime
    ends_at: datetime
    status: str
    cancelled_reason: str | None = None
    notes: str | None = None
    customer: CalendarCustomerOut
    service: CalendarServiceOut | None
    location_id: str


class CalendarOut(BaseModel):
    items: list[CalendarItemOut]


def _to_service_out(service) -> ServiceOut:
    return ServiceOut(
        id=str(service.id),
        tenant_id=str(service.tenant_id),
        name=service.name,
        price_cents=service.price_cents,
        duration_minutes=service.duration_minutes,
        is_active=service.is_active,
    )


def _to_appointment_out(appointment) -> AppointmentOut:
    return AppointmentOut(
        id=str(appointment.id),
        tenant_id=str(appointment.tenant_id),
        customer_id=str(appointment.customer_id),
        location_id=str(appointment.location_id),
        service_id=str(appointment.service_id) if appointment.service_id else None,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        status=appointment.status,
        cancelled_reason=appointment.cancelled_reason,
        status_updated_at=appointment.status_updated_at,
        notes=appointment.notes,
        created_by_user_id=str(appointment.created_by_user_id) if appointment.created_by_user_id else None,
        updated_by_user_id=str(appointment.updated_by_user_id) if appointment.updated_by_user_id else None,
        created_at=appointment.created_at,
    )


def _to_calendar_item_out(item) -> CalendarItemOut:
    service = None
    if item.service_id:
        service = CalendarServiceOut(
            id=str(item.service_id),
            name=item.service_name or "",
            duration_min=item.service_duration_min,
            price=(item.service_price_cents / 100) if item.service_price_cents is not None else None,
        )

    return CalendarItemOut(
        id=str(item.id),
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        status=item.status,
        cancelled_reason=item.cancelled_reason,
        notes=item.notes,
        customer=CalendarCustomerOut(
            id=str(item.customer_id),
            name=item.customer_name,
            phone=item.customer_phone,
        ),
        service=service,
        location_id=str(item.location_id),
    )


@router.get("/services", response_model=ServiceListOut)
def list_services(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    query: str | None = None,
    include_inactive: bool = Query(default=False),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = ServicesRepo(session)
        items, total = repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            query=query,
            include_inactive=include_inactive,
            sort=sort,
            order=order,
        )
        return ServiceListOut(
            items=[_to_service_out(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.post("/services", response_model=ServiceOut)
def create_service(payload: ServiceIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    if payload.name is None or payload.price_cents is None or payload.duration_minutes is None:
        raise HTTPException(status_code=400, detail="name, price_cents and duration_minutes are required")

    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = ServicesRepo(session)
        s = repo.create(tenant_id, ServiceCreate(**payload.model_dump(exclude_none=True)))
        return _to_service_out(s)


@router.patch("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id: str, payload: ServiceIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    with db_session() as session:
        repo = ServicesRepo(session)
        try:
            s = repo.update(tenant_id=tenant_id, service_id=uuid.UUID(service_id), fields=fields)
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=err.message)
        return _to_service_out(s)


@router.delete("/services/{service_id}")
def delete_service(service_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = ServicesRepo(session)
        try:
            repo.delete(tenant_id=tenant_id, service_id=uuid.UUID(service_id))
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=err.message)
    return {"ok": True}


@router.get("/appointments", response_model=AppointmentListOut)
def list_appointments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    query: str | None = None,
    status: str | None = None,
    sort: str = Query(default="starts_at"),
    order: str = Query(default="asc"),
    from_dt: datetime = Query(...),
    to_dt: datetime = Query(...),
    location_id: str | None = None,
    customer_id: str | None = None,
    service_id: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    if from_dt >= to_dt:
        raise HTTPException(status_code=400, detail="from_dt must be before to_dt")

    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = AppointmentsRepo(session)
        try:
            parsed_location_id = uuid.UUID(location_id) if location_id else None
            parsed_customer_id = uuid.UUID(customer_id) if customer_id else None
            parsed_service_id = uuid.UUID(service_id) if service_id else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid location_id, customer_id, or service_id")
        items, total = repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            query=query,
            status=status,
            sort=sort,
            order=order,
            from_dt=from_dt,
            to_dt=to_dt,
            location_id=parsed_location_id,
            customer_id=parsed_customer_id,
            service_id=parsed_service_id,
        )
        return AppointmentListOut(
            items=[_to_appointment_out(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/calendar", response_model=CalendarOut)
def list_calendar(
    from_dt: datetime = Query(...),
    to_dt: datetime = Query(...),
    location_id: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    if from_dt >= to_dt:
        raise HTTPException(status_code=400, detail="from_dt must be before to_dt")

    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = AppointmentsRepo(session)
        try:
            parsed_location_id = uuid.UUID(location_id) if location_id else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid location_id")

        items = repo.list_calendar(
            tenant_id=tenant_id,
            from_dt=from_dt,
            to_dt=to_dt,
            location_id=parsed_location_id,
        )
        return CalendarOut(items=[_to_calendar_item_out(item) for item in items])


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(
    payload: AppointmentCreateIn,
    _tenant=Depends(require_tenant_header),
    identity=Depends(require_user),
):
    tenant_id = uuid.UUID(require_tenant_id())
    try:
        customer_id = uuid.UUID(payload.customer_id)
        location_uuid = uuid.UUID(payload.location_id)
        service_uuid = uuid.UUID(payload.service_id) if payload.service_id else None
        user_uuid = uuid.UUID(identity["user_id"]) if identity and identity.get("user_id") else None
    except ValueError:
        raise ValidationError("invalid_uuid")

    with db_session() as session:
        repo = AppointmentsRepo(session)
        try:
            a = repo.create(
                tenant_id,
                AppointmentCreate(
                    customer_id=customer_id,
                    location_id=location_uuid,
                    service_id=service_uuid,
                    starts_at=payload.starts_at,
                    ends_at=payload.ends_at,
                    status=payload.status,
                    notes=payload.notes,
                    cancelled_reason=payload.cancelled_reason,
                    created_by_user_id=user_uuid,
                    updated_by_user_id=user_uuid,
                ),
            )
        except AppointmentOverlapError as err:
            return JSONResponse(
                status_code=409,
                content={"error": "APPOINTMENT_OVERLAP", "conflicts": err.conflicts},
            )
        return _to_appointment_out(a)


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdateIn,
    _tenant=Depends(require_tenant_header),
    identity=Depends(require_user),
):
    tenant_id = uuid.UUID(require_tenant_id())
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise ValidationError("no_fields_provided")

    try:
        appointment_uuid = uuid.UUID(appointment_id)
        if "customer_id" in fields and fields["customer_id"] is not None:
            fields["customer_id"] = uuid.UUID(fields["customer_id"])
        if "location_id" in fields and fields["location_id"] is not None:
            fields["location_id"] = uuid.UUID(fields["location_id"])
        if "service_id" in fields and fields["service_id"] is not None:
            fields["service_id"] = uuid.UUID(fields["service_id"])
        fields["updated_by_user_id"] = uuid.UUID(identity["user_id"]) if identity and identity.get("user_id") else None
    except ValueError:
        raise ValidationError("invalid_uuid")

    with db_session() as session:
        repo = AppointmentsRepo(session)
        try:
            a = repo.update(tenant_id=tenant_id, appointment_id=appointment_uuid, fields=fields)
        except AppointmentOverlapError as err:
            return JSONResponse(
                status_code=409,
                content={"error": "APPOINTMENT_OVERLAP", "conflicts": err.conflicts},
            )
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=err.message)
        return _to_appointment_out(a)


@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = AppointmentsRepo(session)
        try:
            repo.delete(tenant_id=tenant_id, appointment_id=uuid.UUID(appointment_id))
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=err.message)
    return {"ok": True}
