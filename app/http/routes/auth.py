from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from core.tenancy import require_tenant_id
from core.errors import UnauthorizedError
from core.config import get_config
from app.auth_tokens import issue_token

from app.http.deps import require_tenant_header
from modules.iam.service.auth_service import AuthService


router = APIRouter()


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class AuthOut(BaseModel):
    user_id: str
    token: str


@router.post("/register", response_model=AuthOut)
def register(payload: RegisterIn, request: Request, _tenant=Depends(require_tenant_header)):
    c = request.app.state.container
    tenant_id = require_tenant_id()
    if not c.tenant_service.exists(tenant_id):
        c.tenant_service.create_tenant(tenant_id, name=tenant_id)

    svc = AuthService(c.users_repo, c.billing)
    user = svc.register(email=str(payload.email), password=payload.password)

    cfg = get_config()
    token = issue_token(secret=cfg.SECRET_KEY, tenant_id=tenant_id, user_id=user.id)
    return AuthOut(user_id=user.id, token=token)


@router.post("/login", response_model=AuthOut)
def login(payload: RegisterIn, request: Request, _tenant=Depends(require_tenant_header)):
    c = request.app.state.container
    svc = AuthService(c.users_repo, c.billing)

    try:
        user = svc.authenticate(email=str(payload.email), password=payload.password)
    except UnauthorizedError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    cfg = get_config()
    token = issue_token(secret=cfg.SECRET_KEY, tenant_id=require_tenant_id(), user_id=user.id)
    return AuthOut(user_id=user.id, token=token)
