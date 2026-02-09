import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, EmailStr, Field
from app.http.deps import require_tenant_header, require_user
from modules.crm.models import PipelineStage

from core.tenancy import require_tenant_id
from core.db.session import db_session

from modules.crm.repo_services import ServicesRepo, ServiceCreate
from modules.crm.repo_appointments import AppointmentsRepo, AppointmentCreate

router = APIRouter()


class CreateCustomerIn(BaseModel):
    name: str
    phone: str | None = None
    email: EmailStr | None = None
    tags: list[str] = []
    consent_marketing: bool = False


class UpdateCustomerIn(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    tags: list[str] | None = None
    consent_marketing: bool | None = None


class AddInteractionIn(BaseModel):
    type: str
    content: str


class MoveStageIn(BaseModel):
    to_stage: PipelineStage


class CustomerListOut(BaseModel):
    items: list[dict]
    total: int
    limit: int
    offset: int


@router.post("/customers")
def create_customer(payload: CreateCustomerIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.create_customer(
        name=payload.name,
        phone=payload.phone,
        email=str(payload.email) if payload.email else None,
        tags=set(payload.tags),
        consent_marketing=payload.consent_marketing,
    )
    return {
        "id": cust.id,
        "name": cust.name,
        "phone": cust.phone,
        "email": cust.email,
        "tags": list(cust.tags),
        "stage": cust.stage.value,
        "consent_marketing": cust.consent_marketing,
    }


@router.get("/customers", response_model=CustomerListOut)
def list_customers(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    c = request.app.state.container
    customers = c.crm.list_customers(limit=limit, offset=offset, search=search)
    total = c.crm.count_customers(search=search)
    return {
        "items": [
            {
                "id": cust.id,
                "name": cust.name,
                "phone": cust.phone,
                "email": cust.email,
                "tags": list(cust.tags),
                "stage": cust.stage.value,
                "consent_marketing": cust.consent_marketing,
                "created_at": cust.created_at.isoformat(),
            }
            for cust in customers
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/customers/{customer_id}")
def get_customer(customer_id: str, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.get_customer(customer_id=customer_id)
    return {
        "id": cust.id,
        "name": cust.name,
        "phone": cust.phone,
        "email": cust.email,
        "tags": list(cust.tags),
        "stage": cust.stage.value,
        "consent_marketing": cust.consent_marketing,
        "created_at": cust.created_at.isoformat(),
    }


@router.patch("/customers/{customer_id}")
def update_customer(
    customer_id: str,
    payload: UpdateCustomerIn,
    request: Request,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    c = request.app.state.container
    cust = c.crm.update_customer(
        customer_id=customer_id,
        name=payload.name,
        phone=payload.phone,
        email=str(payload.email) if payload.email else None,
        tags=set(payload.tags) if payload.tags is not None else None,
        consent_marketing=payload.consent_marketing,
    )
    return {
        "id": cust.id,
        "name": cust.name,
        "phone": cust.phone,
        "email": cust.email,
        "tags": list(cust.tags),
        "stage": cust.stage.value,
        "consent_marketing": cust.consent_marketing,
    }


@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: str, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    c.crm.delete_customer(customer_id=customer_id)
    return {"status": "deleted"}


@router.post("/customers/{customer_id}/interactions")
def add_interaction(customer_id: str, payload: AddInteractionIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    i = c.crm.add_interaction(customer_id=customer_id, type=payload.type, content=payload.content)
    return {"id": i.id, "type": i.type, "content": i.content}


@router.get("/customers/{customer_id}/interactions")
def list_interactions(customer_id: str, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    interactions = c.crm.list_interactions(customer_id=customer_id)
    return [
        {
            "id": i.id,
            "type": i.type,
            "content": i.content,
            "created_at": i.created_at.isoformat(),
        }
        for i in interactions
    ]


@router.post("/customers/{customer_id}/stage")
def move_stage(customer_id: str, payload: MoveStageIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.move_stage(customer_id=customer_id, to_stage=payload.to_stage)
    return {"id": cust.id, "stage": cust.stage.value}



##### service and appointments

class ServiceIn(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    price_cents: int | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=1)


class ServiceOut(BaseModel):
    id: str
    tenant_id: uuid
    name: str
    price_cents: int
    duration_minutes: int


class AppointmentIn(BaseModel):
    customer_id: str
    service_id: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: str = "booked"
    notes: str | None = None


class AppointmentOut(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    service_id: str | None
    starts_at: datetime
    ends_at: datetime
    status: str
    notes: str | None


@router.get("/services", response_model=list[ServiceOut])
def list_services(_tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = ServicesRepo(session)
        items = repo.list()
        return [
            ServiceOut(
                id=str(s.id),
                tenant_id=str(s.tenant_id),
                name=s.name,
                price_cents=s.price_cents,
                duration_minutes=s.duration_minutes,
            )
            for s in items
        ]


@router.post("/services", response_model=ServiceOut)
def create_service(payload: ServiceIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = ServicesRepo(session)
        s = repo.create(tenant_id, ServiceCreate(**payload.model_dump()))
        session.commit()
        return ServiceOut(
            id=str(s.id),
            tenant_id=str(s.tenant_id),
            name=s.name,
            price_cents=s.price_cents,
            duration_minutes=s.duration_minutes,
        )


@router.patch("/services/{service_id}", response_model=ServiceOut)
def update_service(service_id: str, payload: ServiceIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}

    with db_session() as session:
        repo = ServicesRepo(session)
        s = repo.update(uuid.UUID(service_id), fields)
        session.commit()
        return ServiceOut(
            id=str(s.id),
            tenant_id=str(s.tenant_id),
            name=s.name,
            price_cents=s.price_cents,
            duration_minutes=s.duration_minutes,
        )


@router.delete("/services/{service_id}")
def delete_service(service_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    with db_session() as session:
        repo = ServicesRepo(session)
        repo.delete(uuid.UUID(service_id))
        session.commit()
    return {"ok": True}


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(from_dt: datetime | None = None, to_dt: datetime | None = None, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    with db_session() as session:
        repo = AppointmentsRepo(session)
        items = repo.list(from_dt=from_dt, to_dt=to_dt)
        return [
            AppointmentOut(
                id=str(a.id),
                tenant_id=str(a.tenant_id),
                customer_id=str(a.customer_id),
                service_id=str(a.service_id) if a.service_id else None,
                starts_at=a.starts_at,
                ends_at=a.ends_at,
                status=a.status,
                notes=a.notes,
            )
            for a in items
        ]


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(payload: AppointmentIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = AppointmentsRepo(session)
        a = repo.create(
            tenant_id,
            AppointmentCreate(
                customer_id=uuid.UUID(payload.customer_id),
                service_id=uuid.UUID(payload.service_id) if payload.service_id else None,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                status=payload.status,
                notes=payload.notes,
            ),
        )
        session.commit()
        return AppointmentOut(
            id=str(a.id),
            tenant_id=str(a.tenant_id),
            customer_id=str(a.customer_id),
            service_id=str(a.service_id) if a.service_id else None,
            starts_at=a.starts_at,
            ends_at=a.ends_at,
            status=a.status,
            notes=a.notes,
        )


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: str, payload: AppointmentIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    fields = payload.model_dump()
    fields["customer_id"] = uuid.UUID(fields["customer_id"])
    fields["service_id"] = uuid.UUID(fields["service_id"]) if fields["service_id"] else None

    with db_session() as session:
        repo = AppointmentsRepo(session)
        a = repo.update(uuid.UUID(appointment_id), fields)
        session.commit()
        return AppointmentOut(
            id=str(a.id),
            tenant_id=str(a.tenant_id),
            customer_id=str(a.customer_id),
            service_id=str(a.service_id) if a.service_id else None,
            starts_at=a.starts_at,
            ends_at=a.ends_at,
            status=a.status,
            notes=a.notes,
        )


@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    with db_session() as session:
        repo = AppointmentsRepo(session)
        repo.delete(uuid.UUID(appointment_id))
        session.commit()
    return {"ok": True}