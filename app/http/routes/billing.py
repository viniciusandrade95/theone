from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.http.deps import require_tenant_header, require_user
from modules.billing.models import PlanTier

router = APIRouter()


class SetPlanIn(BaseModel):
    tier: PlanTier


@router.get("/status")
def status(request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    # dataclasses -> dict
    s = c.billing.plan_status()
    return {
        "tenant_id": s.tenant_id,
        "tier": s.tier.value,
        "active": s.active,
        "whatsapp_enabled": s.whatsapp_enabled,
        "automations_enabled": s.automations_enabled,
        "users": {"current": s.users.current, "max": s.users.max},
        "customers": {"current": s.customers.current, "max": s.customers.max},
        "automations": {"current": s.automations.current, "max": s.automations.max},
    }


@router.post("/plan")
def set_plan(payload: SetPlanIn, request: Request, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    c = request.app.state.container
    sub = c.billing.set_plan(tier=payload.tier)
    return {"tenant_id": sub.tenant_id, "tier": sub.tier.value, "active": sub.active}
