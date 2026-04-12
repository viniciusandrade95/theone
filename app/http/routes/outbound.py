import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.http.deps import require_tenant_header, require_user
from core.db.session import db_session
from core.errors import NotFoundError, ValidationError
from core.tenancy import require_tenant_id
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.tenants.models.tenant_settings_orm import TenantSettingsORM
from modules.messaging.repo.outbound_sql import OutboundRepo
from modules.messaging.service.outbound_renderer import (
    RenderResult,
    ensure_zoneinfo,
    format_appointment_date_time,
    normalize_channel,
    normalize_type,
    render_template,
    validate_final_body,
    validate_template_body,
)
from modules.messaging.models.outbound_message_orm import OutboundMessageORM
from sqlalchemy import select

from core.observability.metrics import inc_counter


router = APIRouter()


def _to_template_out(tpl) -> dict:
    return {
        "id": str(tpl.id),
        "tenant_id": str(tpl.tenant_id),
        "name": tpl.name,
        "type": tpl.type,
        "channel": tpl.channel,
        "body": tpl.body,
        "is_active": bool(tpl.is_active),
        "created_at": tpl.created_at,
        "updated_at": tpl.updated_at,
    }


def _to_message_out(msg) -> dict:
    return {
        "id": str(msg.id),
        "tenant_id": str(msg.tenant_id),
        "customer_id": str(msg.customer_id),
        "appointment_id": str(msg.appointment_id) if msg.appointment_id else None,
        "template_id": str(msg.template_id) if msg.template_id else None,
        "type": msg.type,
        "channel": msg.channel,
        "rendered_body": msg.rendered_body,
        "status": msg.status,
        "error_message": msg.error_message,
        "sent_by_user_id": str(msg.sent_by_user_id) if msg.sent_by_user_id else None,
        "sent_at": msg.sent_at,
        "created_at": msg.created_at,
        "updated_at": msg.updated_at,
    }


def _require_customer(session, tenant_id: uuid.UUID, customer_id: str) -> CustomerORM:
    try:
        cid = uuid.UUID(customer_id)
    except ValueError:
        raise ValidationError("invalid_customer_id")
    customer = session.get(CustomerORM, cid)
    if customer is None or customer.tenant_id != tenant_id or customer.deleted_at is not None:
        raise NotFoundError("customer_not_found", meta={"customer_id": customer_id})
    return customer


def _resolve_appointment(
    session,
    *,
    tenant_id: uuid.UUID,
    appointment_id: str | None,
    customer_id: uuid.UUID,
) -> AppointmentORM | None:
    if appointment_id is None:
        return None
    try:
        aid = uuid.UUID(appointment_id)
    except ValueError:
        raise ValidationError("invalid_appointment_id")
    appt = session.get(AppointmentORM, aid)
    if appt is None or appt.tenant_id != tenant_id or appt.deleted_at is not None:
        raise NotFoundError("appointment_not_found", meta={"appointment_id": appointment_id})
    if appt.customer_id != customer_id:
        raise ValidationError("appointment_customer_mismatch")
    return appt


def _build_context(session, *, tenant_id: uuid.UUID, customer: CustomerORM, appointment: AppointmentORM | None) -> dict[str, str | None]:
    business_name = None
    tenant_settings = session.get(TenantSettingsORM, tenant_id)
    if tenant_settings is not None:
        business_name = tenant_settings.business_name

    context: dict[str, str | None] = {
        "customer_name": customer.name,
        "business_name": business_name or None,
        "appointment_date": None,
        "appointment_time": None,
        "service_name": None,
        "location_name": None,
    }

    if appointment is None:
        return context

    location = session.get(LocationORM, appointment.location_id) if appointment.location_id else None
    tz = ensure_zoneinfo(getattr(location, "timezone", None) if location else None)

    appt_date, appt_time = format_appointment_date_time(starts_at=appointment.starts_at, tz=tz)
    context["appointment_date"] = appt_date
    context["appointment_time"] = appt_time

    if location is not None:
        context["location_name"] = location.name

    if appointment.service_id is not None:
        service = session.get(ServiceORM, appointment.service_id)
        if service is not None:
            context["service_name"] = service.name

    return context


def _normalize_phone_for_wa(phone: str) -> str | None:
    raw = (phone or "").strip()
    if not raw:
        return None
    # wa.me expects country code + number, digits only
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 8:
        return None
    return digits


def _whatsapp_deeplink(*, phone_digits: str, text: str) -> str:
    encoded = urllib.parse.quote(text)
    return f"https://wa.me/{phone_digits}?text={encoded}"


class TemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: str = Field(min_length=1, max_length=64)
    channel: str = Field(default="whatsapp", min_length=1, max_length=32)
    body: str = Field(min_length=1, max_length=2000)
    is_active: bool = True


class TemplatePatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: str | None = Field(default=None, min_length=1, max_length=64)
    channel: str | None = Field(default=None, min_length=1, max_length=32)
    body: str | None = Field(default=None, min_length=1, max_length=2000)
    is_active: bool | None = None


class TemplateListOut(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


@router.get("/outbound/templates", response_model=TemplateListOut)
def list_templates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    type: str | None = None,
    is_active: bool | None = None,
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = OutboundRepo(session)
        items, total = repo.list_templates(
            tenant_id=tenant_id,
            type=type.strip() if type else None,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
        return {"items": [_to_template_out(t) for t in items], "total": total, "page": page, "page_size": page_size}


@router.post("/outbound/templates")
def create_template(payload: TemplateIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    t_type = normalize_type(payload.type)
    channel = normalize_channel(payload.channel)
    validate_template_body(payload.body)
    name = payload.name.strip()
    with db_session() as session:
        repo = OutboundRepo(session)
        tpl = repo.create_template(
            tenant_id=tenant_id,
            name=name,
            type=t_type,
            channel=channel,
            body=payload.body.strip(),
            is_active=payload.is_active,
        )
        return _to_template_out(tpl)


@router.get("/outbound/templates/{template_id}")
def get_template(template_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = OutboundRepo(session)
        tpl = repo.get_template(tenant_id=tenant_id, template_id=template_id)
        return _to_template_out(tpl)


@router.patch("/outbound/templates/{template_id}")
def patch_template(template_id: str, payload: TemplatePatchIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    patch = payload.model_dump(exclude_unset=True)
    if not patch:
        raise ValidationError("no_fields_provided")
    normalized: dict[str, object] = {}
    if "name" in patch:
        normalized["name"] = str(patch["name"]).strip()
    if "type" in patch:
        normalized["type"] = normalize_type(str(patch["type"]))
    if "channel" in patch:
        normalized["channel"] = normalize_channel(str(patch["channel"]))
    if "body" in patch:
        body = str(patch["body"]).strip()
        validate_template_body(body)
        normalized["body"] = body
    if "is_active" in patch:
        normalized["is_active"] = bool(patch["is_active"])
    with db_session() as session:
        repo = OutboundRepo(session)
        tpl = repo.update_template(tenant_id=tenant_id, template_id=template_id, patch=normalized)
        return _to_template_out(tpl)


@router.delete("/outbound/templates/{template_id}")
def delete_template(template_id: str, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = OutboundRepo(session)
        repo.delete_template(tenant_id=tenant_id, template_id=template_id)
    return {"ok": True}


class PreviewIn(BaseModel):
    customer_id: str
    appointment_id: str | None = None
    template_id: str | None = None
    type: str | None = None
    body: str | None = Field(default=None, max_length=2000)


class PreviewOut(BaseModel):
    rendered_body: str
    variables_used: list[str]


@router.post("/outbound/preview", response_model=PreviewOut)
def preview(payload: PreviewIn, _tenant=Depends(require_tenant_header), _user=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = OutboundRepo(session)
        customer = _require_customer(session, tenant_id, payload.customer_id)
        appointment = _resolve_appointment(
            session,
            tenant_id=tenant_id,
            appointment_id=payload.appointment_id,
            customer_id=customer.id,
        )

        template = None
        body = payload.body
        t_type = payload.type
        if payload.template_id:
            template = repo.get_template(tenant_id=tenant_id, template_id=payload.template_id)
            if not template.is_active:
                raise ValidationError("template_inactive")
            body = template.body
            t_type = template.type

        if not body:
            raise ValidationError("body is required")
        if not t_type:
            raise ValidationError("type is required")

        _ = normalize_type(t_type)
        context = _build_context(session, tenant_id=tenant_id, customer=customer, appointment=appointment)
        rendered: RenderResult = render_template(body=body, context=context)
        return PreviewOut(rendered_body=rendered.rendered_body, variables_used=rendered.variables_used)


class SendIn(BaseModel):
    customer_id: str
    appointment_id: str | None = None
    template_id: str | None = None
    final_body: str | None = Field(default=None, max_length=2000)
    type: str
    channel: str = Field(default="whatsapp")


class SendOut(BaseModel):
    ok: bool
    outbound_message: dict
    whatsapp_url: str | None = None
    note: str | None = None


@router.post("/outbound/send", response_model=SendOut)
def send(payload: SendIn, request: Request, _tenant=Depends(require_tenant_header), identity=Depends(require_user)):
    tenant_id_str = require_tenant_id()
    tenant_id = uuid.UUID(tenant_id_str)
    channel = normalize_channel(payload.channel)
    t_type = normalize_type(payload.type)

    user_id = None
    if identity and identity.get("user_id"):
        try:
            user_id = uuid.UUID(identity["user_id"])
        except ValueError:
            user_id = None

    with db_session() as session:
        repo = OutboundRepo(session)
        customer = _require_customer(session, tenant_id, payload.customer_id)
        appointment = _resolve_appointment(
            session,
            tenant_id=tenant_id,
            appointment_id=payload.appointment_id,
            customer_id=customer.id,
        )

        template = None
        template_id_uuid = None
        rendered_body = None
        if payload.template_id:
            template = repo.get_template(tenant_id=tenant_id, template_id=payload.template_id)
            template_id_uuid = template.id
            if not template.is_active:
                raise ValidationError("template_inactive")
            if template.type != t_type:
                raise ValidationError("template_type_mismatch")
            if template.channel != channel:
                raise ValidationError("template_channel_mismatch")
            context = _build_context(session, tenant_id=tenant_id, customer=customer, appointment=appointment)
            rendered_body = render_template(body=template.body, context=context).rendered_body

        if payload.final_body is not None:
            # user override (must be valid and not empty)
            rendered_body = validate_final_body(payload.final_body)

        if rendered_body is None:
            raise ValidationError("final_body_or_template_required")

        # required contact for whatsapp deeplink
        phone_digits = _normalize_phone_for_wa(customer.phone or "")
        if phone_digits is None:
            failed = repo.create_message(
                tenant_id=tenant_id,
                customer_id=customer.id,
                appointment_id=appointment.id if appointment else None,
                template_id=template_id_uuid,
                type=t_type,
                channel=channel,
                rendered_body=rendered_body,
                status="failed",
                error_message="customer_missing_valid_phone",
                sent_by_user_id=user_id,
                sent_at=None,
            )
            inc_counter(
                "outbound_send_total",
                labels={"status": "failed", "channel": channel, "type": t_type},
            )
            return SendOut(ok=False, outbound_message=_to_message_out(failed), whatsapp_url=None, note="Customer has no valid phone for WhatsApp.")

        # prepare link
        whatsapp_url = _whatsapp_deeplink(phone_digits=phone_digits, text=rendered_body)

        # NOTE: in MVP, status='sent' means "assistido" (user initiated), not provider delivery confirmation.
        # Cheap dedupe for double-clicks: same customer + same body within a short window.
        now_utc = datetime.now(timezone.utc)
        window_start = now_utc - timedelta(seconds=10)
        stmt = (
            select(OutboundMessageORM)
            .where(OutboundMessageORM.tenant_id == tenant_id)
            .where(OutboundMessageORM.customer_id == customer.id)
            .where(OutboundMessageORM.rendered_body == rendered_body)
            .where(OutboundMessageORM.status == "sent")
            .where(OutboundMessageORM.created_at >= window_start)
        )
        existing = session.execute(stmt).scalars().first()
        if existing is not None:
            inc_counter(
                "outbound_send_total",
                labels={"status": "sent", "channel": channel, "type": t_type},
            )
            return SendOut(
                ok=True,
                outbound_message=_to_message_out(existing),
                whatsapp_url=whatsapp_url,
                note="Duplicate send prevented (same body).",
            )
        sent_at = now_utc
        msg = repo.create_message(
            tenant_id=tenant_id,
            customer_id=customer.id,
            appointment_id=appointment.id if appointment else None,
            template_id=template_id_uuid,
            type=t_type,
            channel=channel,
            rendered_body=rendered_body,
            status="sent",
            error_message=None,
            sent_by_user_id=user_id,
            sent_at=sent_at,
        )
        inc_counter(
            "outbound_send_total",
            labels={"status": "sent", "channel": channel, "type": t_type},
        )

        # side effect: interaction only when status=sent
        request.app.state.container.crm.add_interaction(
            customer_id=str(customer.id),
            type="outbound_whatsapp",
            content=rendered_body,
        )

        return SendOut(
            ok=True,
            outbound_message=_to_message_out(msg),
            whatsapp_url=whatsapp_url,
            note="MVP: 'sent' means user-assisted send initiated (not provider delivery confirmation).",
        )


@router.post("/outbound/{message_id}/resend", response_model=SendOut)
def resend(message_id: str, request: Request, _tenant=Depends(require_tenant_header), identity=Depends(require_user)):
    tenant_id = uuid.UUID(require_tenant_id())
    user_id = None
    if identity and identity.get("user_id"):
        try:
            user_id = uuid.UUID(identity["user_id"])
        except ValueError:
            user_id = None

    with db_session() as session:
        repo = OutboundRepo(session)
        msg = repo.get_message(tenant_id=tenant_id, message_id=message_id)
        if msg.status != "failed":
            raise ValidationError("resend_only_failed")

        customer = session.get(CustomerORM, msg.customer_id)
        if customer is None or customer.tenant_id != tenant_id or customer.deleted_at is not None:
            raise NotFoundError("customer_not_found", meta={"customer_id": str(msg.customer_id)})

        phone_digits = _normalize_phone_for_wa(customer.phone or "")
        if phone_digits is None:
            repo.mark_failed(tenant_id=tenant_id, message_id=message_id, error_message="customer_missing_valid_phone")
            inc_counter(
                "outbound_send_total",
                labels={"status": "failed", "channel": msg.channel, "type": msg.type},
            )
            return SendOut(ok=False, outbound_message=_to_message_out(msg), whatsapp_url=None, note="Customer has no valid phone for WhatsApp.")

        whatsapp_url = _whatsapp_deeplink(phone_digits=phone_digits, text=msg.rendered_body)
        repo.mark_sent(tenant_id=tenant_id, message_id=message_id)
        inc_counter(
            "outbound_send_total",
            labels={"status": "sent", "channel": msg.channel, "type": msg.type},
        )

        request.app.state.container.crm.add_interaction(
            customer_id=str(customer.id),
            type="outbound_whatsapp",
            content=msg.rendered_body,
        )

        return SendOut(
            ok=True,
            outbound_message=_to_message_out(msg),
            whatsapp_url=whatsapp_url,
            note="MVP: 'sent' means user-assisted send initiated (not provider delivery confirmation).",
        )


class MessageListOut(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


@router.get("/outbound/messages", response_model=MessageListOut)
def list_messages(
    customer_id: str | None = None,
    template_id: str | None = None,
    type: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    _tenant=Depends(require_tenant_header),
    _user=Depends(require_user),
):
    tenant_id = uuid.UUID(require_tenant_id())
    with db_session() as session:
        repo = OutboundRepo(session)
        items, total = repo.list_messages(
            tenant_id=tenant_id,
            customer_id=customer_id,
            template_id=template_id,
            type=type.strip() if type else None,
            status=status.strip() if status else None,
            page=page,
            page_size=page_size,
        )
        return {"items": [_to_message_out(m) for m in items], "total": total, "page": page, "page_size": page_size}
