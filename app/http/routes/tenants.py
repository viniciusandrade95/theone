from fastapi import APIRouter, Request
from pydantic import BaseModel

from modules.tenants.service.tenant_service import TenantService

router = APIRouter()


class CreateTenantRequest(BaseModel):
    id: str
    name: str


@router.post("")
def create_tenant(req: CreateTenantRequest, request: Request):
    container = request.app.state.container
    service = container.tenant_service

    tenant = service.create_tenant(req.id, req.name)

    return {
        "id": tenant.id,
        "name": tenant.name,
    }
