from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel
from app.http.deps import require_tenant_header
from core.tenancy import require_tenant_id
from core.events import MessageReceived

router = APIRouter()


class InboundIn(BaseModel):
    message_id: str
    from_phone: str
    text: str


@router.post("/inbound")
def inbound(payload: InboundIn, background: BackgroundTasks, request: Request, _tenant=Depends(require_tenant_header)):
    c = request.app.state.container
    tenant_id = require_tenant_id()

    background.add_task(
        c.bus.publish,
        MessageReceived(tenant_id=tenant_id, payload=payload.model_dump()),
    )
    return {"status": "accepted"}
