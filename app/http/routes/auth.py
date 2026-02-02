import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field

from core.tenancy import require_tenant_id, set_tenant_id, clear_tenant_id
from core.config import get_config
from app.auth_tokens import issue_token
from core.db.session import db_session

from app.http.deps import require_tenant_header, require_user
from modules.iam.service.auth_service import AuthService


router = APIRouter()


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class AuthOut(BaseModel):
    user_id: str
    tenant_id: str
    email: EmailStr
    token: str


class SignupIn(BaseModel):
    tenant_name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)


class SignupOut(BaseModel):
    tenant_id: str
    user_id: str
    email: EmailStr
    token: str

class MeOut(BaseModel):
    user_id: str
    tenant_id: str
    email: EmailStr

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
    return AuthOut(user_id=user.id, tenant_id=tenant_id, email=user.email, token=token)


@router.post("/signup", response_model=SignupOut)
def signup(payload: SignupIn, request: Request):
    c = request.app.state.container

    tenant_id = str(uuid.uuid4())
    set_tenant_id(tenant_id)
    try:
        with db_session():
            tenant = c.tenant_service.create_tenant(tenant_id, name=payload.tenant_name)
            svc = AuthService(c.users_repo, c.billing)
            user = svc.register(email=str(payload.email), password=payload.password)
    finally:
        clear_tenant_id()

    cfg = get_config()
    token = issue_token(secret=cfg.SECRET_KEY, tenant_id=tenant.id, user_id=user.id)
    return SignupOut(tenant_id=tenant.id, user_id=user.id, email=user.email, token=token)


@router.post("/login", response_model=AuthOut)
def login(payload: RegisterIn, request: Request, _tenant=Depends(require_tenant_header)):
    c = request.app.state.container
    svc = AuthService(c.users_repo, c.billing)

    user = svc.authenticate(email=str(payload.email), password=payload.password)

    cfg = get_config()
    tenant_id = require_tenant_id()
    token = issue_token(secret=cfg.SECRET_KEY, tenant_id=tenant_id, user_id=user.id)
    return AuthOut(user_id=user.id, tenant_id=tenant_id, email=user.email, token=token)


@router.get("/me", response_model=MeOut)
def me(request: Request, _tenant=Depends(require_tenant_header), identity=Depends(require_user)):
    c = request.app.state.container
    svc = AuthService(c.users_repo, c.billing)
    user = svc.get_user(user_id=identity["user_id"])
    tenant_id = require_tenant_id()
    return MeOut(user_id=user.id, tenant_id=tenant_id, email=user.email)
