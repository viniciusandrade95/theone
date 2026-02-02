from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from modules.tenants.service.tenant_service import TenantService
from app.http.deps import require_tenant_header, require_user

router = APIRouter()


class CreateTenantRequest(BaseModel):
    id: str
    name: str


@router.post("")
def create_tenant(
    req: CreateTenantRequest,
    request: Request,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    container = request.app.state.container
    service = container.tenant_service

    tenant = service.create_tenant(req.id, req.name)

    return {
        "id": tenant.id,
        "name": tenant.name,
    }
