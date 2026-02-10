from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import load_config, get_config
from core.tenancy import set_tenant_id, clear_tenant_id
from core.auth import clear_current_user_id
from core.errors import to_http_error, from_http_exception
from core.errors.base import AppError
from core.db.session import reset_engine_state

from app.container import build_container
from app.http.routes.auth import router as auth_router
from app.http.routes.crm import router as crm_router
from app.http.routes.analytics import router as analytics_router
from app.http.routes.billing import router as billing_router
from app.http.routes.messaging import router as messaging_router
from app.http.routes.tenants import router as tenants_router


def create_app() -> FastAPI:
    load_config()
    cfg = get_config()

    if cfg.ENV == "test" and cfg.DATABASE_URL == "dev":
        reset_engine_state()

    app = FastAPI(title=cfg.APP_NAME)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.CORS_ALLOW_ORIGINS),
        allow_origin_regex=cfg.CORS_ALLOW_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    container = build_container()
    app.state.container = container

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        http_err = to_http_error(exc)
        return JSONResponse(status_code=http_err.status_code, content=http_err.body)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        normalized = from_http_exception(status_code=exc.status_code, detail=exc.detail)
        return JSONResponse(status_code=normalized.status_code, content=normalized.body)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        normalized_errors: list[dict[str, object]] = []
        fields: dict[str, str] = {}
        for err in exc.errors():
            loc = err.get("loc") or []
            msg = str(err.get("msg") or "Invalid value")
            normalized_errors.append(
                {
                    "loc": [str(item) for item in loc],
                    "msg": msg,
                    "type": str(err.get("type") or "validation_error"),
                }
            )
            if len(loc) >= 2 and loc[0] in {"body", "query", "path"}:
                field = str(loc[-1])
                fields.setdefault(field, msg)

        details = {"errors": normalized_errors}
        if fields:
            details["fields"] = fields

        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "details": details,
            },
        )

    @app.middleware("http")
    async def tenancy_middleware(request: Request, call_next):
        clear_current_user_id()
        # CORS preflight requests do not include tenant headers.
        if request.method == "OPTIONS":
            return await call_next(request)
       
        if request.url.path in ("/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        PUBLIC_PATHS = {
            "/auth/signup",
            "/auth/login_email",
            "/auth/select_workspace",
        }

        if request.url.path.startswith("/messaging/inbound") or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        
        clear_tenant_id()

        tenant_header = cfg.TENANT_HEADER
        tenant_id = request.headers.get(tenant_header)

        try:
            if not tenant_id:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "VALIDATION_ERROR",
                        "details": {"message": f"Missing tenant header: {tenant_header}"},
                    },
                )

            container = request.app.state.container
            #if request.url.path != "/auth/register":
            #    container.tenant_service.get_or_fail(tenant_id)
            set_tenant_id(tenant_id)

            return await call_next(request)
        except Exception as err:
            http_err = to_http_error(err)
            return JSONResponse(status_code=http_err.status_code, content=http_err.body)
        finally:
            clear_tenant_id()
            clear_current_user_id()

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(crm_router, prefix="/crm", tags=["crm"])
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(billing_router, prefix="/billing", tags=["billing"])
    app.include_router(messaging_router, prefix="/messaging", tags=["messaging"])
    app.include_router(tenants_router, prefix="/tenants", tags=["tenants"])

    return app

def app_factory():
    return create_app()


# For uvicorn: "uvicorn app.http.main:app_factory --factory"
app = None  # type: ignore
