from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    # Public root endpoint to avoid tenant-header errors on base URL health checks / browser visits.
    return {"ok": True, "service": "beauty-crm-api"}


@router.get("/healthz")
def healthz():
    return {"ok": True}
