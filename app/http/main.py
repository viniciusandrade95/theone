import time

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
from core.observability.logging import log_event
from core.observability.metrics import inc_counter, observe_histogram
from core.observability.tracing import TRACE_HEADER_NAME, clear_trace_id, ensure_trace_id, get_trace_id
from app.http.routes.auth import router as auth_router
from app.http.routes.crm import router as crm_router
from app.http.routes.analytics import router as analytics_router
from app.http.routes.assistant_analytics import router as assistant_analytics_router
from app.http.routes.billing import router as billing_router
from app.http.routes.messaging import router as messaging_router
from app.http.routes.tenants import router as tenants_router
from app.http.routes.booking import router as booking_router
from app.http.routes.public_booking import router as public_booking_router
from app.http.routes.outbound import router as outbound_router
from app.http.routes.dashboard import router as dashboard_router
from app.http.routes.health import router as health_router
from app.http.routes.chatbot import router as chatbot_router
from app.http.routes.assistant import router as assistant_router
from app.http.routes.metrics import router as metrics_router


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
    try:
        from tasks.queue import set_container_override

        set_container_override(container)
    except Exception:
        # Best-effort; do not fail app startup if Celery/task module is not available.
        pass

    ASSISTANT_SURFACE_PATHS = {"/api/chatbot/message", "/api/chatbot/reset", "/crm/assistant/prebook"}

    def _inject_trace_id_if_assistant(request: Request, body: dict) -> dict:
        if request.url.path in ASSISTANT_SURFACE_PATHS and "trace_id" not in body:
            body = dict(body)
            body["trace_id"] = get_trace_id()
        return body

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        http_err = to_http_error(exc)
        return JSONResponse(
            status_code=http_err.status_code,
            content=_inject_trace_id_if_assistant(request, http_err.body),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        normalized = from_http_exception(status_code=exc.status_code, detail=exc.detail)
        return JSONResponse(
            status_code=normalized.status_code,
            content=_inject_trace_id_if_assistant(request, normalized.body),
        )

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
            content=_inject_trace_id_if_assistant(
                request,
                {
                    "error": "VALIDATION_ERROR",
                    "details": details,
                },
            ),
        )

    @app.middleware("http")
    async def tenancy_middleware(request: Request, call_next):
        clear_current_user_id()
        # CORS preflight requests do not include tenant headers.
        if request.method == "OPTIONS":
            return await call_next(request)
       
        if request.url.path in ("/", "/docs", "/openapi.json", "/redoc", "/healthz", "/favicon.ico", "/metrics"):
            return await call_next(request)

        PUBLIC_PATHS = {
            "/auth/signup",
            "/auth/login_email",
            "/auth/select_workspace",
        }

        if (
            request.url.path.startswith("/messaging/inbound")
            or request.url.path.startswith("/messaging/delivery")
            or request.url.path.startswith("/messaging/webhook")
            or request.url.path.startswith("/public/book")
            or request.url.path in PUBLIC_PATHS
        ):
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

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        # Trace id is always present after this point.
        trace_id = ensure_trace_id(request)
        request.state.trace_id = trace_id

        started = time.perf_counter()
        log_event(
            "http_request_started",
            method=request.method,
            path=request.url.path,
        )
        status_code = 500
        route_template = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[TRACE_HEADER_NAME] = trace_id
            return response
        finally:
            duration_s = max(0.0, time.perf_counter() - started)
            duration_ms = int(duration_s * 1000)
            route_obj = request.scope.get("route")
            route_template = getattr(route_obj, "path", None) if route_obj is not None else None
            route_label = route_template or "unmatched"

            # Metrics: baseline HTTP.
            inc_counter(
                "http_requests_total",
                labels={"route": route_label, "method": request.method, "status": str(status_code)},
            )
            observe_histogram(
                "http_request_duration_seconds",
                labels={"route": route_label, "method": request.method},
                value=duration_s,
            )

            # Metrics: assistant operational surface.
            surface = None
            if request.url.path == "/api/chatbot/message":
                surface = "chatbot_message"
            elif request.url.path == "/api/chatbot/reset":
                surface = "chatbot_reset"
            elif request.url.path == "/crm/assistant/prebook":
                surface = "prebook"
            if surface is not None:
                if 200 <= status_code < 300:
                    outcome = "success"
                elif status_code in {401, 403}:
                    outcome = "unauthorized"
                elif status_code == 409:
                    outcome = "conflict"
                else:
                    outcome = "error"
                inc_counter("assistant_requests_total", labels={"surface": surface, "outcome": outcome})
                observe_histogram("assistant_request_duration_seconds", labels={"surface": surface}, value=duration_s)

            log_event(
                "http_request_completed",
                method=request.method,
                path=request.url.path,
                route=route_template,
                status_code=status_code,
                duration_ms=duration_ms,
            )

            clear_trace_id()
            clear_current_user_id()
            clear_tenant_id()

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(crm_router, prefix="/crm", tags=["crm"])
    app.include_router(assistant_router, prefix="/crm", tags=["assistant"])
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(assistant_analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(billing_router, prefix="/billing", tags=["billing"])
    app.include_router(messaging_router, prefix="/messaging", tags=["messaging"])
    app.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
    app.include_router(booking_router, prefix="/crm", tags=["crm"])
    app.include_router(outbound_router, prefix="/crm", tags=["crm"])
    app.include_router(dashboard_router, prefix="/crm", tags=["crm"])
    app.include_router(health_router, tags=["health"])
    app.include_router(public_booking_router, tags=["public"])
    app.include_router(chatbot_router, prefix="/api/chatbot", tags=["chatbot"])
    app.include_router(metrics_router, tags=["metrics"])

    return app

def app_factory():
    return create_app()


# For uvicorn: "uvicorn app.http.main:app_factory --factory"
app = None  # type: ignore
