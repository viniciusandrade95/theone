from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from core.config import get_config
from modules.messaging.providers import verify_signature
from tasks.queue import enqueue_inbound_webhook

router = APIRouter()


class InboundIn(BaseModel):
    provider: str = Field(default="meta")
    external_event_id: str
    phone_number_id: str
    message_id: str
    from_phone: str
    text: str
    to_phone: str | None = None


@router.post("/inbound")
async def inbound(payload: InboundIn, request: Request):
    cfg = get_config()
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(secret=cfg.WHATSAPP_WEBHOOK_SECRET or "", payload=body, signature_header=signature):
        raise HTTPException(status_code=401, detail="invalid_signature")

    container = request.app.state.container
    account = container.messaging_repo.get_whatsapp_account(
        provider=payload.provider, phone_number_id=payload.phone_number_id
    )
    if account is None:
        raise HTTPException(status_code=404, detail="whatsapp_account_not_found")

    try:
        enqueue_inbound_webhook(payload=payload.model_dump(), signature_valid=True)
    except Exception:
        raise HTTPException(status_code=503, detail="queue_unavailable")
    return {"status": "accepted"}
