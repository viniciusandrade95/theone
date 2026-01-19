from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr
from app.http.deps import require_tenant_header, require_user
from modules.crm.models import PipelineStage

router = APIRouter()


class CreateCustomerIn(BaseModel):
    name: str
    phone: str | None = None
    email: EmailStr | None = None
    tags: list[str] = []


class AddInteractionIn(BaseModel):
    type: str
    content: str


class MoveStageIn(BaseModel):
    to_stage: PipelineStage


@router.post("/customers")
def create_customer(payload: CreateCustomerIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.create_customer(
        name=payload.name,
        phone=payload.phone,
        email=str(payload.email) if payload.email else None,
        tags=set(payload.tags),
    )
    return {
        "id": cust.id,
        "name": cust.name,
        "phone": cust.phone,
        "email": cust.email,
        "tags": list(cust.tags),
        "stage": cust.stage.value,
    }


@router.post("/customers/{customer_id}/interactions")
def add_interaction(customer_id: str, payload: AddInteractionIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    i = c.crm.add_interaction(customer_id=customer_id, type=payload.type, content=payload.content)
    return {"id": i.id, "type": i.type, "content": i.content}


@router.post("/customers/{customer_id}/stage")
def move_stage(customer_id: str, payload: MoveStageIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    cust = c.crm.move_stage(customer_id=customer_id, to_stage=payload.to_stage)
    return {"id": cust.id, "stage": cust.stage.value}
