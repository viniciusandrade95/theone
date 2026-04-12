from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config.loader import get_config
from core.observability.logging import log_event
from core.observability.metrics import inc_counter
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.customer_orm import CustomerORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.messaging.models.message_template_orm import MessageTemplateORM
from modules.messaging.models.outbound_message_orm import OutboundMessageORM
from modules.messaging.models.whatsapp_account_orm import WhatsAppAccountORM
from modules.messaging.providers.meta_whatsapp_cloud import MetaWhatsAppCloudProvider
from modules.messaging.providers.smtp_email import SmtpEmailProvider
from modules.messaging.repo.outbound_sql import OutboundRepo
from modules.messaging.service.outbound_renderer import ensure_zoneinfo, format_appointment_date_time, render_template
from modules.tenants.models.tenant_settings_orm import TenantSettingsORM


class AssistantCommunicationService:
    """
    Minimal automation layer: send confirmation messages for assistant/business events.

    Goals:
    - Reuse outbound templates as the source of truth for message content.
    - Prefer provider-backed delivery when possible.
    - Be idempotent-ish via outbound idempotency_key.
    - Never fail the caller's business action when messaging fails.
    """

    def __init__(self, session: Session):
        self.session = session
        self.outbound = OutboundRepo(session)

    def confirm_prebook_created(
        self,
        *,
        tenant_id: uuid.UUID,
        appointment_id: uuid.UUID,
        customer_id: uuid.UUID,
        trace_id: str,
        conversation_id: uuid.UUID | None = None,
        assistant_session_id: str | None = None,
    ) -> OutboundMessageORM | None:
        return self._send_confirmation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            appointment_id=appointment_id,
            trace_id=trace_id,
            trigger_type="assistant_prebook_created",
            template_type="assistant_prebook_confirmation",
            idempotency_scope=f"assistant_prebook_confirmation:{appointment_id}",
            conversation_id=conversation_id,
            assistant_session_id=assistant_session_id,
        )

    def confirm_handoff_created(
        self,
        *,
        tenant_id: uuid.UUID,
        handoff_id: uuid.UUID,
        customer_id: uuid.UUID | None,
        trace_id: str,
        conversation_id: uuid.UUID | None = None,
        assistant_session_id: str | None = None,
    ) -> OutboundMessageORM | None:
        if customer_id is None:
            log_event(
                "assistant_confirmation_skipped_missing_customer",
                tenant_id=str(tenant_id),
                trace_id=trace_id,
                handoff_id=str(handoff_id),
            )
            return None
        return self._send_confirmation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            appointment_id=None,
            trace_id=trace_id,
            trigger_type="assistant_handoff_created",
            template_type="assistant_handoff_confirmation",
            idempotency_scope=f"assistant_handoff_confirmation:{handoff_id}",
            conversation_id=conversation_id,
            assistant_session_id=assistant_session_id,
        )

    def _send_confirmation(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        appointment_id: uuid.UUID | None,
        trace_id: str,
        trigger_type: str,
        template_type: str,
        idempotency_scope: str,
        conversation_id: uuid.UUID | None,
        assistant_session_id: str | None,
    ) -> OutboundMessageORM | None:
        customer = self._require_customer(tenant_id=tenant_id, customer_id=customer_id)
        appointment = self._resolve_appointment(tenant_id=tenant_id, appointment_id=appointment_id, customer_id=customer_id)
        context = self._build_context(tenant_id=tenant_id, customer=customer, appointment=appointment)

        # Deterministic preference order: WhatsApp -> Email.
        candidates: list[str] = ["whatsapp", "email"]

        for channel in candidates:
            template = self._get_active_template(tenant_id=tenant_id, type=template_type, channel=channel)
            if template is None:
                continue

            try:
                rendered = render_template(body=template.body, context=context).rendered_body
            except Exception as err:
                log_event(
                    "assistant_confirmation_render_failed",
                    level="warning",
                    tenant_id=str(tenant_id),
                    trace_id=trace_id,
                    trigger_type=trigger_type,
                    template_type=template_type,
                    channel=channel,
                    error=str(err),
                )
                continue

            idempotency_key = f"auto:{idempotency_scope}:{channel}"
            existing = self.outbound.get_by_idempotency_key(tenant_id=tenant_id, idempotency_key=idempotency_key)
            if existing is not None:
                if (existing.status or "").strip().lower() != "failed":
                    log_event(
                        "assistant_confirmation_idempotent_hit",
                        tenant_id=str(tenant_id),
                        trace_id=trace_id,
                        trigger_type=trigger_type,
                        outbound_message_id=str(existing.id),
                        channel=existing.channel,
                        type=existing.type,
                    )
                    return existing

                # Hardening: allow retry/fallback when a previous attempt was recorded as failed.
                # This avoids a permanently stuck "failed" idempotency hit and enables later recovery.
                log_event(
                    "assistant_confirmation_retry_failed_idempotency",
                    level="warning",
                    tenant_id=str(tenant_id),
                    trace_id=trace_id,
                    trigger_type=trigger_type,
                    outbound_message_id=str(existing.id),
                    channel=existing.channel,
                    type=existing.type,
                )
                existing.template_id = template.id
                existing.type = template.type
                existing.channel = channel
                existing.rendered_body = rendered
                existing.trace_id = trace_id
                existing.conversation_id = conversation_id
                existing.assistant_session_id = assistant_session_id
                existing.status = "pending"
                existing.error_message = None
                existing.error_code = None
                existing.delivery_status = "queued"
                existing.delivery_status_updated_at = datetime.now(timezone.utc)
                self.session.add(existing)
                self.session.flush()

                msg = existing
            else:
                msg = self._create_outbound_row(
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    appointment_id=appointment_id,
                    template=template,
                    channel=channel,
                    rendered_body=rendered,
                    idempotency_key=idempotency_key,
                    trigger_type=trigger_type,
                    trace_id=trace_id,
                    conversation_id=conversation_id,
                    assistant_session_id=assistant_session_id,
                )

            ok = False
            if channel == "whatsapp":
                ok = self._send_whatsapp(tenant_id=tenant_id, msg=msg, customer=customer, trace_id=trace_id)
            elif channel == "email":
                ok = self._send_email(tenant_id=tenant_id, msg=msg, customer=customer, trace_id=trace_id, subject=template.name)

            if ok:
                return msg

        # No usable template/channel succeeded.
        log_event(
            "assistant_confirmation_failed",
            level="warning",
            tenant_id=str(tenant_id),
            trace_id=trace_id,
            trigger_type=trigger_type,
            template_type=template_type,
        )
        return None

    def _require_customer(self, *, tenant_id: uuid.UUID, customer_id: uuid.UUID) -> CustomerORM:
        row = self.session.get(CustomerORM, customer_id)
        if row is None or row.tenant_id != tenant_id or row.deleted_at is not None:
            raise ValueError("customer_not_found_or_cross_tenant")
        return row

    def _resolve_appointment(
        self,
        *,
        tenant_id: uuid.UUID,
        appointment_id: uuid.UUID | None,
        customer_id: uuid.UUID,
    ) -> AppointmentORM | None:
        if appointment_id is None:
            return None
        appt = self.session.get(AppointmentORM, appointment_id)
        if appt is None or appt.tenant_id != tenant_id or appt.deleted_at is not None:
            return None
        if appt.customer_id != customer_id:
            return None
        return appt

    def _get_active_template(self, *, tenant_id: uuid.UUID, type: str, channel: str) -> MessageTemplateORM | None:
        stmt = (
            select(MessageTemplateORM)
            .where(MessageTemplateORM.tenant_id == tenant_id)
            .where(MessageTemplateORM.type == type)
            .where(MessageTemplateORM.channel == channel)
            .where(MessageTemplateORM.is_active.is_(True))
            .order_by(MessageTemplateORM.updated_at.desc(), MessageTemplateORM.id.asc())
        )
        return self.session.execute(stmt).scalars().first()

    def _build_context(
        self,
        *,
        tenant_id: uuid.UUID,
        customer: CustomerORM,
        appointment: AppointmentORM | None,
    ) -> dict[str, str | None]:
        business_name = None
        tenant_settings = self.session.get(TenantSettingsORM, tenant_id)
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

        location = self.session.get(LocationORM, appointment.location_id) if appointment.location_id else None
        tz = ensure_zoneinfo(getattr(location, "timezone", None) if location else None)
        appt_date, appt_time = format_appointment_date_time(starts_at=appointment.starts_at, tz=tz)
        context["appointment_date"] = appt_date
        context["appointment_time"] = appt_time

        if location is not None:
            context["location_name"] = location.name

        if appointment.service_id is not None:
            service = self.session.get(ServiceORM, appointment.service_id)
            if service is not None:
                context["service_name"] = service.name

        return context

    def _create_outbound_row(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        appointment_id: uuid.UUID | None,
        template: MessageTemplateORM,
        channel: str,
        rendered_body: str,
        idempotency_key: str,
        trigger_type: str,
        trace_id: str,
        conversation_id: uuid.UUID | None,
        assistant_session_id: str | None,
    ) -> OutboundMessageORM:
        now = datetime.now(timezone.utc)
        try:
            # Important: isolate uniqueness conflicts without rolling back the whole request transaction.
            with self.session.begin_nested():
                msg = self.outbound.create_message(
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    appointment_id=appointment_id,
                    template_id=template.id,
                    type=template.type,
                    channel=channel,
                    rendered_body=rendered_body,
                    status="pending",
                    error_message=None,
                    sent_by_user_id=None,
                    sent_at=None,
                    recipient=None,
                    delivery_status="queued",
                    delivery_status_updated_at=now,
                    idempotency_key=idempotency_key,
                    trigger_type=trigger_type,
                    trace_id=trace_id,
                    conversation_id=conversation_id,
                    assistant_session_id=assistant_session_id,
                )
            log_event(
                "assistant_confirmation_requested",
                tenant_id=str(tenant_id),
                trace_id=trace_id,
                trigger_type=trigger_type,
                outbound_message_id=str(msg.id),
                channel=channel,
                type=template.type,
            )
            return msg
        except IntegrityError:
            existing = self.outbound.get_by_idempotency_key(tenant_id=tenant_id, idempotency_key=idempotency_key)
            if existing is None:
                raise
            return existing

    def _normalize_phone_for_wa(self, phone: str) -> str | None:
        raw = (phone or "").strip()
        if not raw:
            return None
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) < 8:
            return None
        return digits

    def _send_whatsapp(self, *, tenant_id: uuid.UUID, msg: OutboundMessageORM, customer: CustomerORM, trace_id: str) -> bool:
        phone_digits = self._normalize_phone_for_wa(customer.phone or "")
        if phone_digits is None:
            self.outbound.mark_failed(tenant_id=tenant_id, message_id=str(msg.id), error_message="customer_missing_valid_phone")
            msg.error_code = "missing_recipient"
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "failed", "channel": "whatsapp", "type": msg.type})
            return False

        account = self.session.execute(
            select(WhatsAppAccountORM)
            .where(WhatsAppAccountORM.tenant_id == tenant_id)
            .where(WhatsAppAccountORM.provider == "meta")
            .where(WhatsAppAccountORM.status == "active")
            .order_by(WhatsAppAccountORM.created_at.asc())
        ).scalars().first()
        provider_enabled = bool(getattr(get_config(), "WHATSAPP_CLOUD_ACCESS_TOKEN", None)) and account is not None
        if not provider_enabled or account is None:
            self.outbound.mark_failed(tenant_id=tenant_id, message_id=str(msg.id), error_message="whatsapp_provider_not_configured")
            msg.error_code = "provider_not_configured"
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "failed", "channel": "whatsapp", "type": msg.type})
            return False

        provider = MetaWhatsAppCloudProvider()
        try:
            res = provider.send_whatsapp_text(
                phone_number_id=account.phone_number_id,
                to_phone=phone_digits,
                body=msg.rendered_body,
                trace_id=trace_id,
                idempotency_key=msg.idempotency_key,
            )
            now = datetime.now(timezone.utc)
            msg.provider = res.provider
            msg.provider_message_id = res.provider_message_id
            msg.recipient = phone_digits
            msg.delivery_status = "accepted"
            msg.delivery_status_updated_at = now
            msg.status = "sent"
            msg.sent_at = now
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "sent", "channel": "whatsapp", "type": msg.type})
            log_event(
                "assistant_confirmation_sent",
                tenant_id=str(tenant_id),
                trace_id=trace_id,
                outbound_message_id=str(msg.id),
                channel="whatsapp",
                provider=res.provider,
            )
            return True
        except Exception as err:
            self.outbound.mark_failed(tenant_id=tenant_id, message_id=str(msg.id), error_message=str(err))
            msg.error_code = "provider_send_failed"
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "failed", "channel": "whatsapp", "type": msg.type})
            log_event(
                "assistant_confirmation_send_failed",
                level="warning",
                tenant_id=str(tenant_id),
                trace_id=trace_id,
                outbound_message_id=str(msg.id),
                channel="whatsapp",
                error=str(err),
            )
            return False

    def _send_email(
        self,
        *,
        tenant_id: uuid.UUID,
        msg: OutboundMessageORM,
        customer: CustomerORM,
        trace_id: str,
        subject: str,
    ) -> bool:
        email = (customer.email or "").strip().lower()
        if not email or "@" not in email:
            self.outbound.mark_failed(tenant_id=tenant_id, message_id=str(msg.id), error_message="customer_missing_valid_email")
            msg.error_code = "missing_recipient"
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "failed", "channel": "email", "type": msg.type})
            return False

        provider = SmtpEmailProvider.from_config(get_config())
        if provider is None:
            self.outbound.mark_failed(tenant_id=tenant_id, message_id=str(msg.id), error_message="email_provider_not_configured")
            msg.error_code = "provider_not_configured"
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "failed", "channel": "email", "type": msg.type})
            return False

        try:
            res = provider.send_email_text(
                to_email=email,
                subject=subject or "Confirmação",
                body=msg.rendered_body,
                trace_id=trace_id,
                idempotency_key=msg.idempotency_key,
            )
            now = datetime.now(timezone.utc)
            msg.provider = res.provider
            msg.provider_message_id = res.provider_message_id
            msg.recipient = email
            msg.delivery_status = "sent"
            msg.delivery_status_updated_at = now
            msg.status = "sent"
            msg.sent_at = now
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "sent", "channel": "email", "type": msg.type})
            log_event(
                "assistant_confirmation_sent",
                tenant_id=str(tenant_id),
                trace_id=trace_id,
                outbound_message_id=str(msg.id),
                channel="email",
                provider=res.provider,
            )
            return True
        except Exception as err:
            self.outbound.mark_failed(tenant_id=tenant_id, message_id=str(msg.id), error_message=str(err))
            msg.error_code = "provider_send_failed"
            self.session.add(msg)
            self.session.flush()
            inc_counter("outbound_send_total", labels={"status": "failed", "channel": "email", "type": msg.type})
            log_event(
                "assistant_confirmation_send_failed",
                level="warning",
                tenant_id=str(tenant_id),
                trace_id=trace_id,
                outbound_message_id=str(msg.id),
                channel="email",
                error=str(err),
            )
            return False
