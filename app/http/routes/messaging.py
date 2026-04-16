import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from core.config import get_config
from core.observability.logging import log_event
from core.observability.metrics import inc_counter
from core.errors import ConflictError
from core.tenancy import clear_tenant_id, require_tenant_id, set_tenant_id
from app.http.deps import require_tenant_admin
from modules.messaging.models import WhatsAppAccount
from modules.messaging.providers import verify_signature
from modules.messaging.service.outbound_delivery_service import OutboundDeliveryService
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


class WhatsAppAccountIn(BaseModel):
    provider: str = Field(default="meta")
    phone_number_id: str
    status: str = Field(default="active")


async def _require_valid_whatsapp_signature(request: Request) -> bytes:
    """Validate Meta webhook HMAC signature and return raw request body bytes.

    `WHATSAPP_WEBHOOK_SECRET` is expected to be the Meta App Secret.
    """
    cfg = get_config()
    secret = (cfg.WHATSAPP_WEBHOOK_SECRET or "").strip()
    if not secret:
        inc_counter("messaging_whatsapp_webhook_rejected_total", labels={"reason": "missing_secret"})
        log_event("messaging_whatsapp_webhook_rejected", level="error", reason="missing_secret", path=request.url.path)
        raise HTTPException(status_code=503, detail="whatsapp_webhook_secret_not_configured")
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(secret=secret, payload=body, signature_header=signature):
        reason = "missing_signature" if not signature else "invalid_signature"
        inc_counter("messaging_whatsapp_webhook_rejected_total", labels={"reason": reason})
        log_event("messaging_whatsapp_webhook_rejected", level="warning", reason=reason, path=request.url.path)
        raise HTTPException(status_code=401, detail="invalid_signature")
    return body


@router.get("/webhook")
async def whatsapp_webhook_verify(request: Request):
    """WhatsApp Cloud webhook verification (Meta).

    Meta sends a GET with:
    - hub.mode=subscribe
    - hub.verify_token=<token you configured>
    - hub.challenge=<random>
    """
    cfg = get_config()
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    expected = (cfg.WHATSAPP_WEBHOOK_VERIFY_TOKEN or "").strip()
    if not expected:
        inc_counter("messaging_whatsapp_webhook_verify_total", labels={"outcome": "error", "reason": "missing_verify_token"})
        log_event("messaging_whatsapp_webhook_verify_error", level="error", reason="missing_verify_token")
        raise HTTPException(status_code=503, detail="whatsapp_verify_token_not_configured")
    if mode != "subscribe" or not token or token != expected:
        inc_counter("messaging_whatsapp_webhook_verify_total", labels={"outcome": "rejected", "reason": "invalid_verify_token"})
        log_event("messaging_whatsapp_webhook_verify_rejected", level="warning", reason="invalid_verify_token")
        raise HTTPException(status_code=403, detail="whatsapp_verify_token_invalid")
    inc_counter("messaging_whatsapp_webhook_verify_total", labels={"outcome": "ok"})
    return PlainTextResponse(content=(challenge or ""))


def _iter_meta_changes(payload: dict) -> list[dict]:
    entries = payload.get("entry")
    if not isinstance(entries, list):
        return []
    changes: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw_changes = entry.get("changes")
        if not isinstance(raw_changes, list):
            continue
        for change in raw_changes:
            if isinstance(change, dict):
                changes.append(change)
    return changes


def _extract_meta_inbound_events(payload: dict) -> list[dict]:
    events: list[dict] = []
    for change in _iter_meta_changes(payload):
        value = change.get("value")
        if not isinstance(value, dict):
            continue
        metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
        phone_number_id = (metadata.get("phone_number_id") or "").strip()
        to_phone = metadata.get("display_phone_number")

        messages = value.get("messages")
        if not isinstance(messages, list):
            continue
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            msg_id = (msg.get("id") or "").strip()
            from_phone = (msg.get("from") or "").strip()
            text_obj = msg.get("text") if isinstance(msg.get("text"), dict) else None
            body = text_obj.get("body") if isinstance(text_obj, dict) else None
            body = body.strip() if isinstance(body, str) else ""
            if not msg_id or not from_phone or not body or not phone_number_id:
                continue
            events.append(
                {
                    "provider": "meta",
                    "external_event_id": msg_id,
                    "phone_number_id": phone_number_id,
                    "message_id": msg_id,
                    "from_phone": from_phone,
                    "to_phone": to_phone,
                    "text": body,
                }
            )
    return events


def _extract_meta_delivery_events(payload: dict) -> list[dict]:
    events: list[dict] = []
    for change in _iter_meta_changes(payload):
        value = change.get("value")
        if not isinstance(value, dict):
            continue
        metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
        phone_number_id = (metadata.get("phone_number_id") or "").strip()
        if not phone_number_id:
            continue

        statuses = value.get("statuses")
        if not isinstance(statuses, list):
            continue
        for st in statuses:
            if not isinstance(st, dict):
                continue
            provider_message_id = (st.get("id") or "").strip()
            status = (st.get("status") or "").strip().lower()
            ts = (st.get("timestamp") or "").strip()
            if not provider_message_id or not status:
                continue
            error_code = None
            errors = st.get("errors")
            if isinstance(errors, list) and errors and isinstance(errors[0], dict):
                code = errors[0].get("code")
                if code is not None:
                    error_code = str(code)
            external_event_id = f"{provider_message_id}:{status}:{ts or '0'}"
            events.append(
                {
                    "provider": "meta",
                    "external_event_id": external_event_id,
                    "phone_number_id": phone_number_id,
                    "provider_message_id": provider_message_id,
                    "channel": "whatsapp",
                    "status": status,
                    "error_code": error_code,
                    "payload": st,
                }
            )
    return events


@router.post("/webhook")
async def whatsapp_webhook(payload: dict, request: Request):
    """WhatsApp Cloud webhook (Meta) entrypoint.

    Configure this route in Meta Webhooks:
    - inbound messages -> enqueued for async processing (+ bot reply)
    - delivery statuses -> processed inline (delivery lifecycle)
    """
    await _require_valid_whatsapp_signature(request)

    inbound_events = _extract_meta_inbound_events(payload)
    delivery_events = _extract_meta_delivery_events(payload)

    inc_counter("messaging_whatsapp_webhook_accepted_total", labels={"type": "meta"})
    inc_counter("messaging_whatsapp_inbound_events_total", value=len(inbound_events))
    inc_counter("messaging_whatsapp_delivery_events_total", value=len(delivery_events))
    log_event(
        "messaging_whatsapp_webhook_parsed",
        inbound_events=len(inbound_events),
        delivery_events=len(delivery_events),
    )

    for event in inbound_events:
        enqueue_inbound_webhook(payload=event, signature_valid=True)

    from core.db.session import db_session  # local import to avoid cycles

    container = request.app.state.container
    recorded = 0
    updated = 0
    unknown_accounts = 0
    for event in delivery_events:
        account = container.messaging_repo.get_whatsapp_account(provider=event["provider"], phone_number_id=event["phone_number_id"])
        if account is None:
            unknown_accounts += 1
            continue
        clear_tenant_id()
        set_tenant_id(account.tenant_id)
        with db_session() as session:
            res = OutboundDeliveryService(session).ingest_event(
                tenant_id=uuid.UUID(account.tenant_id),
                provider=event["provider"],
                external_event_id=event["external_event_id"],
                provider_message_id=event.get("provider_message_id"),
                channel=event.get("channel") or "whatsapp",
                status=event.get("status") or "unknown",
                error_code=event.get("error_code"),
                payload=event.get("payload"),
            )
        clear_tenant_id()
        if res.get("recorded"):
            recorded += 1
        if res.get("updated_message_id"):
            updated += 1

    return {
        "status": "accepted",
        "inbound_enqueued": len(inbound_events),
        "delivery_recorded": recorded,
        "delivery_updated": updated,
        "delivery_unknown_accounts": unknown_accounts,
    }


@router.post("/inbound")
async def inbound(payload: InboundIn, request: Request):
    await _require_valid_whatsapp_signature(request)

    container = request.app.state.container
    account = container.messaging_repo.get_whatsapp_account(
        provider=payload.provider, phone_number_id=payload.phone_number_id
    )
    if account is None:
        inc_counter("messaging_whatsapp_inbound_rejected_total", labels={"reason": "unknown_account"})
        log_event("messaging_whatsapp_inbound_rejected", level="warning", reason="unknown_account")
        raise HTTPException(status_code=404, detail="whatsapp_account_not_found")

    try:
        enqueue_inbound_webhook(payload=payload.model_dump(), signature_valid=True)
    except Exception:
        inc_counter("messaging_whatsapp_inbound_rejected_total", labels={"reason": "queue_unavailable"})
        raise HTTPException(status_code=503, detail="queue_unavailable")
    inc_counter("messaging_whatsapp_inbound_accepted_total")
    return {"status": "accepted"}


class OutboundDeliveryEventIn(BaseModel):
    provider: str = Field(default="meta")
    external_event_id: str
    phone_number_id: str
    provider_message_id: str | None = None
    channel: str = Field(default="whatsapp")
    status: str
    error_code: str | None = None
    payload: dict | None = None


class WhatsAppAccountOut(BaseModel):
    id: str
    tenant_id: str
    provider: str
    phone_number_id: str
    status: str
    created_at: str | None = None


class WhatsAppConnectionStatusOut(BaseModel):
    webhook_secret_configured: bool
    webhook_verify_token_configured: bool
    cloud_access_token_configured: bool
    cloud_api_version: str
    last_delivery_callback_received_at: str | None = None


class WhatsAppAccountsListOut(BaseModel):
    accounts: list[WhatsAppAccountOut]
    connection: WhatsAppConnectionStatusOut


@router.post("/delivery")
async def delivery_event(payload: OutboundDeliveryEventIn, request: Request):
    """Provider callback ingestion for outbound delivery lifecycle.

    - No tenant header is expected (provider-driven).
    - Tenant is resolved via WhatsApp account routing (provider + phone_number_id).
    """
    await _require_valid_whatsapp_signature(request)

    container = request.app.state.container
    account = container.messaging_repo.get_whatsapp_account(provider=payload.provider, phone_number_id=payload.phone_number_id)
    if account is None:
        inc_counter("messaging_whatsapp_delivery_rejected_total", labels={"reason": "unknown_account"})
        log_event("messaging_whatsapp_delivery_rejected", level="warning", reason="unknown_account")
        raise HTTPException(status_code=404, detail="whatsapp_account_not_found")

    clear_tenant_id()
    set_tenant_id(account.tenant_id)

    from core.db.session import db_session  # local import to avoid cycles

    with db_session() as session:
        res = OutboundDeliveryService(session).ingest_event(
            tenant_id=uuid.UUID(account.tenant_id),
            provider=payload.provider,
            external_event_id=payload.external_event_id,
            provider_message_id=payload.provider_message_id,
            channel=payload.channel,
            status=payload.status,
            error_code=payload.error_code,
            payload=payload.payload,
        )

    clear_tenant_id()
    inc_counter("messaging_whatsapp_delivery_accepted_total", labels={"status": (payload.status or "unknown").lower()})
    return {"status": "accepted", **res}


@router.get("/whatsapp-accounts")
def list_whatsapp_accounts(
    request: Request,
    _admin=Depends(require_tenant_admin),
) -> WhatsAppAccountsListOut:
    """List WhatsApp account mappings for the current tenant (admin UX helper).

    TheOne routes provider callbacks by `provider + phone_number_id`. This endpoint helps the
    admin UI show "connected numbers" and basic server readiness signals.
    """
    tenant_id = require_tenant_id()
    cfg = get_config()

    from core.db.session import db_session  # local import to avoid cycles
    from sqlalchemy import select, func
    from modules.messaging.models.whatsapp_account_orm import WhatsAppAccountORM
    from modules.messaging.models.outbound_delivery_event_orm import OutboundDeliveryEventORM

    with db_session() as session:
        stmt = select(WhatsAppAccountORM).where(WhatsAppAccountORM.tenant_id == uuid.UUID(tenant_id)).order_by(
            WhatsAppAccountORM.created_at.desc()
        )
        rows = session.execute(stmt).scalars().all()
        last_delivery_at = session.execute(
            select(func.max(OutboundDeliveryEventORM.received_at)).where(
                OutboundDeliveryEventORM.tenant_id == uuid.UUID(tenant_id)
            )
        ).scalar_one()

    accounts = [
        WhatsAppAccountOut(
            id=str(row.id),
            tenant_id=str(row.tenant_id),
            provider=row.provider,
            phone_number_id=row.phone_number_id,
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else None,
        )
        for row in rows
    ]
    connection = WhatsAppConnectionStatusOut(
        webhook_secret_configured=bool((cfg.WHATSAPP_WEBHOOK_SECRET or "").strip()),
        webhook_verify_token_configured=bool((cfg.WHATSAPP_WEBHOOK_VERIFY_TOKEN or "").strip()),
        cloud_access_token_configured=bool((cfg.WHATSAPP_CLOUD_ACCESS_TOKEN or "").strip()),
        cloud_api_version=cfg.WHATSAPP_CLOUD_API_VERSION,
        last_delivery_callback_received_at=last_delivery_at.isoformat() if last_delivery_at else None,
    )
    return WhatsAppAccountsListOut(accounts=accounts, connection=connection)


@router.post("/whatsapp-accounts")
def create_whatsapp_account(
    payload: WhatsAppAccountIn,
    request: Request,
    _admin=Depends(require_tenant_admin),
):
    tenant_id = require_tenant_id()
    account = WhatsAppAccount.create(
        account_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        provider=payload.provider,
        phone_number_id=payload.phone_number_id,
        status=payload.status,
    )
    try:
        request.app.state.container.messaging_repo.create_whatsapp_account(account)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
    return {
        "id": account.id,
        "tenant_id": account.tenant_id,
        "provider": account.provider,
        "phone_number_id": account.phone_number_id,
        "status": account.status,
    }
