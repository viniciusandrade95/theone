import uuid

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

from core.tenancy import require_tenant_id, set_tenant_id, clear_tenant_id
from core.config import get_config
from app.auth_tokens import issue_token, issue_preauth_token, verify_preauth_token
from core.db.session import db_session
from core.security.hashing import verify_password

from app.http.deps import require_tenant_header, require_user
from modules.crm.repo_locations import LocationsRepo
from modules.iam.service.auth_service import AuthService
from modules.tenants.repo.settings_sql import SqlTenantSettingsRepo


router = APIRouter(tags=["auth"])



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

class LoginEmailIn(BaseModel):
    email: EmailStr
    password: str

class WorkspaceOption(BaseModel):
    tenant_id: UUID
    tenant_name: str

class LoginEmailOut(BaseModel):
    mode: str  # "authenticated" or "select_workspace"
    auth: AuthOut | None = None
    preauth_token: str | None = None
    workspaces: list[WorkspaceOption] | None = None

class SelectWorkspaceIn(BaseModel):
    preauth_token: str
    tenant_id: UUID


def _ensure_default_location(tenant_id: str) -> None:
    with db_session() as session:
        location = LocationsRepo(session).ensure_default_location(tenant_id)
        settings_repo = SqlTenantSettingsRepo(session)
        settings = settings_repo.get_or_create(tenant_id=tenant_id)
        if settings.default_location_id != location.id:
            settings_repo.update(tenant_id=tenant_id, patch={"default_location_id": str(location.id)})


@router.post("/register", response_model=AuthOut)
def register(payload: RegisterIn, request: Request, _tenant=Depends(require_tenant_header)):
    c = request.app.state.container
    tenant_id = require_tenant_id()
    if not c.tenant_service.exists(tenant_id):
        c.tenant_service.create_tenant(tenant_id, name=tenant_id)

    svc = AuthService(c.users_repo, c.billing)
    user = svc.register(email=str(payload.email), password=payload.password)
    _ensure_default_location(tenant_id)

    cfg = get_config()
    token = issue_token(secret=cfg.SECRET_KEY, tenant_id=tenant_id, user_id=user.id)
    return AuthOut(user_id=user.id, tenant_id=tenant_id, email=user.email, token=token)


@router.post("/signup", response_model=SignupOut)
def signup(payload: SignupIn, request: Request):
    c = request.app.state.container

    tenant_id = str(uuid.uuid4())

    # IMPORTANT: set tenant context BEFORE opening db_session()
    set_tenant_id(tenant_id)
    try:
        with db_session() as session:
            tenant = c.tenant_service.create_tenant(tenant_id, name=payload.tenant_name)

            svc = AuthService(c.users_repo, c.billing)
            user = svc.register(email=str(payload.email), password=payload.password)
            LocationsRepo(session).ensure_default_location(tenant.id)
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
    _ensure_default_location(tenant_id)
    token = issue_token(secret=cfg.SECRET_KEY, tenant_id=tenant_id, user_id=user.id)
    return AuthOut(user_id=user.id, tenant_id=tenant_id, email=user.email, token=token)


@router.get("/me", response_model=MeOut)
def me(request: Request, _tenant=Depends(require_tenant_header), identity=Depends(require_user)):
    c = request.app.state.container
    svc = AuthService(c.users_repo, c.billing)
    user = svc.get_user(user_id=identity["user_id"])
    tenant_id = require_tenant_id()
    return MeOut(user_id=user.id, tenant_id=tenant_id, email=user.email)



@router.post("/login_email", response_model=LoginEmailOut)
def login_email(payload: LoginEmailIn, request: Request):
    c = request.app.state.container
    cfg = get_config()

    email = str(payload.email).strip().lower()

    # Global lookup (no tenant header)
    candidates = c.users_repo.list_by_email(email)

    valid = []
    for u in candidates:
        if verify_password(payload.password, u.password_hash):
            valid.append(u)

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if len(valid) == 1:
        u = valid[0]
        _ensure_default_location(u.tenant_id)
        token = issue_token(secret=cfg.SECRET_KEY, tenant_id=u.tenant_id, user_id=u.id)
        return LoginEmailOut(
            mode="authenticated",
            auth=AuthOut(user_id=u.id, tenant_id=u.tenant_id, email=u.email, token=token),
        )

    choices = [{"tenant_id": u.tenant_id, "user_id": u.id} for u in valid]
    preauth = issue_preauth_token(secret=cfg.SECRET_KEY, email=email, choices=choices, ttl_seconds=3600)

    workspaces = []
    for u in valid:
        t = c.tenant_service.get_or_fail(u.tenant_id)
        workspaces.append(WorkspaceOption(tenant_id=t.id, tenant_name=t.name))

    # Deduplicate
    seen = set()
    uniq = []
    for w in workspaces:
        if w.tenant_id not in seen:
            uniq.append(w)
            seen.add(w.tenant_id)

    for w in uniq:
        _ensure_default_location(str(w.tenant_id))

    return LoginEmailOut(mode="select_workspace", preauth_token=preauth, workspaces=uniq)


@router.post("/select_workspace", response_model=AuthOut)
def select_workspace(payload: SelectWorkspaceIn, request: Request):
    cfg = get_config()

    try:
        preauth = verify_preauth_token(secret=cfg.SECRET_KEY, token=payload.preauth_token)
    except ValueError as e:
        # expired / invalid tokens should be treated like "not logged in"
        raise HTTPException(status_code=401, detail=str(e))

    allowed = {c["tenant_id"]: c["user_id"] for c in preauth.choices}
    tenant_id = str(payload.tenant_id)

    if tenant_id not in allowed:
        raise HTTPException(status_code=403, detail="Workspace not allowed")

    user_id = allowed[tenant_id]
    _ensure_default_location(tenant_id)
    token = issue_token(secret=cfg.SECRET_KEY, tenant_id=tenant_id, user_id=user_id)

    return AuthOut(user_id=user_id, tenant_id=tenant_id, email=preauth.email, token=token)
