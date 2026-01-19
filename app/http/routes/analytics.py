from fastapi import APIRouter, Depends, Request
from datetime import datetime
from core.errors import ValidationError
from app.http.deps import require_tenant_header, require_user

router = APIRouter()


def _parse_dt(s: str) -> datetime:
    s = (s or "").strip().replace(" ", "+")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except Exception:
        raise ValidationError("Invalid datetime format. Use ISO 8601, e.g. 2026-01-17T00:00:00+00:00")


@router.get("/summary")
def summary(start: str, end: str, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    s = c.analytics.summary(start=_parse_dt(start), end=_parse_dt(end))
    return s.__dict__
