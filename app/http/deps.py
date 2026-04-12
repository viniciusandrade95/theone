import hmac

from fastapi import Depends, Header, Request
from core.tenancy import set_tenant_id, clear_tenant_id, require_tenant_id
from core.auth import set_current_user_id
from core.config import get_config
from core.errors import UnauthorizedError, ValidationError
from app.auth_tokens import verify_token


def tenant_dependency(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    # Alias acima é fallback; abaixo respeitamos TENANT_HEADER também.
    cfg = get_config()
    tenant_header_name = cfg.TENANT_HEADER

    # Preferir header configurado
    tenant_id = x_tenant_id
    # Se TENANT_HEADER não for X-Tenant-ID, tenta buscar dinamicamente no request (via middleware abaixo).
    # Para manter simples aqui, aceitamos X-Tenant-ID como default; o middleware vai garantir o resto.

    if not tenant_id:
        raise ValidationError("Missing tenant header")

    clear_tenant_id()
    set_tenant_id(tenant_id)
    return tenant_id


def require_user(request: Request, authorization: str | None = Header(default=None)):
    cfg = get_config()
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        parsed = verify_token(secret=cfg.SECRET_KEY, token=token)
    except RuntimeError as e:
        raise UnauthorizedError(str(e))

    # Garante coerência tenant
    tenant_id = require_tenant_id()
    if parsed.tenant_id != tenant_id:
        raise UnauthorizedError("tenant_mismatch")

    set_current_user_id(parsed.user_id)

    # devolve identity mínima
    return {"user_id": parsed.user_id, "tenant_id": parsed.tenant_id}


def require_user_or_assistant_connector(
    request: Request,
    authorization: str | None = Header(default=None),
    x_assistant_token: str | None = Header(default=None, alias="X-Assistant-Token"),
):
    """Authenticate either a logged-in staff user (Bearer) or the chatbot connector (shared secret).

    This is intended for server-to-server calls from `chatbot1` through TheOneConnector.
    """
    if authorization and authorization.startswith("Bearer "):
        identity = require_user(request, authorization=authorization)
        return {"mode": "user", **identity}

    cfg = get_config()
    header_name = (cfg.ASSISTANT_CONNECTOR_HEADER or "X-Assistant-Token").strip() or "X-Assistant-Token"
    expected = cfg.ASSISTANT_CONNECTOR_TOKEN
    # MVP: when the shared secret is not configured, allow calls without the header.
    if not expected:
        tenant_id = require_tenant_id()
        return {"mode": "assistant_connector", "user_id": None, "tenant_id": tenant_id}
    provided = request.headers.get(header_name) or x_assistant_token
    if not provided:
        raise UnauthorizedError("Missing assistant token")
    if not expected or not hmac.compare_digest(provided.strip(), expected):
        raise UnauthorizedError("Invalid assistant token")

    tenant_id = require_tenant_id()
    return {"mode": "assistant_connector", "user_id": None, "tenant_id": tenant_id}


def require_assistant_token(
    request: Request,
    x_assistant_token: str | None = Header(default=None, alias="X-Assistant-Token"),
):
    """Authenticate server-to-server calls (assistant connector) using a shared secret header.

    Header name is configurable via `ASSISTANT_CONNECTOR_HEADER` (default: `X-Assistant-Token`).
    Secret is configured via `ASSISTANT_CONNECTOR_TOKEN`.
    """
    cfg = get_config()
    header_name = (cfg.ASSISTANT_CONNECTOR_HEADER or "X-Assistant-Token").strip() or "X-Assistant-Token"
    expected = cfg.ASSISTANT_CONNECTOR_TOKEN
    # MVP: if secret isn't configured (e.g. local dev), don't enforce the header.
    if not expected:
        return True
    provided = request.headers.get(header_name) or x_assistant_token
    if not provided:
        raise UnauthorizedError("Missing assistant token")
    if not expected or not hmac.compare_digest(provided.strip(), expected):
        raise UnauthorizedError("Invalid assistant token")
    return True


def require_tenant_header(x_tenant_id: str = Header(..., alias="X-Tenant-ID")):
    # O middleware já seta tenancy context. Isto serve para:
    # 1) Documentar no OpenAPI como required
    # 2) Bloquear requests sem header antes de chegar no handler
    if not x_tenant_id:
        raise ValidationError("Missing tenant header")
    return x_tenant_id
