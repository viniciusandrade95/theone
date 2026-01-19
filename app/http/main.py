from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import load_config, get_config
from core.tenancy import set_tenant_id, clear_tenant_id
from core.errors import to_http_error

from app.container import build_container
from app.http.routes.auth import router as auth_router
from app.http.routes.crm import router as crm_router
from app.http.routes.analytics import router as analytics_router
from app.http.routes.billing import router as billing_router
from app.http.routes.messaging import router as messaging_router

load_config()

def create_app() -> FastAPI:
    
    cfg = get_config()

    app = FastAPI(title=cfg.APP_NAME)

    container = build_container()
    app.state.container = container

    @app.middleware("http")
    async def tenancy_middleware(request: Request, call_next):
        clear_tenant_id()

        tenant_header = cfg.TENANT_HEADER
        tenant_id = request.headers.get(tenant_header)

        try:
            if not tenant_id:
                return JSONResponse(
                    status_code=400,
                    content={"error": "validation_error", "message": f"Missing tenant header: {tenant_header}"})

            container = request.app.state.container
            if request.url.path != "/auth/register":
                container.tenant_service.get_or_fail(tenant_id)
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

    return app

def app_factory():
    return create_app()


#app = create_app()

# For uvicorn: "uvicorn app.http.main:app"
app = None  # type: ignore
