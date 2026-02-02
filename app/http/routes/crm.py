from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, EmailStr
from app.http.deps import require_tenant_header, require_user
from modules.crm.models import PipelineStage

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
