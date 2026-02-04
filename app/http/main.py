from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import load_config, get_config
from core.tenancy import set_tenant_id, clear_tenant_id
from core.errors import to_http_error
from core.errors.base import AppError

from app.container import build_container
from app.http.routes.auth import router as auth_router
from app.http.routes.crm import router as crm_router
from app.http.routes.analytics import router as analytics_router
from app.http.routes.billing import router as billing_router
from app.http.routes.messaging import router as messaging_router
from app.http.routes.tenants import router as tenants_router


load_config()

def create_app() -> FastAPI:
    
    cfg = get_config()

    app = FastAPI(title=cfg.APP_NAME)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
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
        return JSONResponse(status_code=exc.status_code, content={"error": "http_error", "message": exc.detail})

    @app.middleware("http")
    async def tenancy_middleware(request: Request, call_next):
       
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
                    content={"error": "validation_error", "message": f"Missing tenant header: {tenant_header}"})

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

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(crm_router, prefix="/crm", tags=["crm"])
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(billing_router, prefix="/billing", tags=["billing"])
    app.include_router(messaging_router, prefix="/messaging", tags=["messaging"])
    app.include_router(tenants_router, prefix="/tenants", tags=["tenants"])

    return app

def app_factory():
    return create_app()


#app = create_app()

# For uvicorn: "uvicorn app.http.main:app"
app = None  # type: ignore
