import uuid
from datetime import datetime, timezone

from core.config import get_config
from core.errors import NotFoundError, ForbiddenError
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.messaging.models import WebhookEvent, Conversation, Message
from modules.messaging.repo.messaging_repo import MessagingRepo
from modules.crm.service import CrmService
from modules.billing.service import BillingService, Feature, assert_allowed
from core.observability.logging import log_event
from core.observability.metrics import inc_counter, start_timer
from modules.chatbot.service.chatbot_client import ChatbotClient
from modules.chatbot.service.normalizer import normalize_chatbot_response
from modules.messaging.providers.meta_whatsapp_cloud import MetaWhatsAppCloudProvider
from modules.messaging.repo.outbound_sql import OutboundRepo


class InboundWebhookService:
    def __init__(self, repo: MessagingRepo, crm: CrmService, billing: BillingService):
        self.repo = repo
        self.crm = crm
        self.billing = billing

    def handle_inbound(self, *, payload: dict, signature_valid: bool) -> dict:
        timer = start_timer()
        provider = payload.get("provider", "").strip().lower()
        phone_number_id = payload.get("phone_number_id", "").strip()
        external_event_id = payload.get("external_event_id", "").strip()
        provider_message_id = payload.get("message_id", "").strip()
        from_phone = payload.get("from_phone", "").strip()
        text = payload.get("text", "").strip()
        to_phone = payload.get("to_phone")

        account = self.repo.get_whatsapp_account(provider=provider, phone_number_id=phone_number_id)
        if account is None:
            raise NotFoundError("whatsapp_account_not_found", meta={"provider": provider, "phone_number_id": phone_number_id})

        clear_tenant_id()
        set_tenant_id(account.tenant_id)
        try:
            if not signature_valid:
                raise ForbiddenError("invalid_signature")
            assert_allowed(self.billing.can_use_feature(Feature.WHATSAPP))
            event = WebhookEvent.create(
                event_id=str(uuid.uuid4()),
                tenant_id=account.tenant_id,
                provider=provider,
                external_event_id=external_event_id,
                payload=payload,
                signature_valid=signature_valid,
                status="received",
            )
            is_new = self.repo.record_webhook_event(event)
            if not is_new:
                return {"status": "duplicate"}

            customer = self.crm.find_customer_by_phone(phone=from_phone)
            if customer is None:
                try:
                    customer = self.crm.create_customer(name=f"WhatsApp {from_phone}", phone=from_phone)
                except Exception:
                    # Best-effort conflict recovery (phone unique): if a concurrent create happened, load again.
                    customer = self.crm.find_customer_by_phone(phone=from_phone)
                if customer is None:
                    raise NotFoundError("customer_not_found", meta={"phone": from_phone})

            conversation = self.repo.get_conversation(
                tenant_id=account.tenant_id,
                customer_id=customer.id,
                channel="whatsapp",
            )
            if conversation is None:
                conversation = Conversation.create(
                    conversation_id=str(uuid.uuid4()),
                    tenant_id=account.tenant_id,
                    customer_id=customer.id,
                    channel="whatsapp",
                )
            conversation = self.repo.upsert_conversation(conversation)

            message = Message.inbound(
                message_id=str(uuid.uuid4()),
                tenant_id=account.tenant_id,
                conversation_id=conversation.id,
                provider=provider,
                provider_message_id=provider_message_id,
                from_phone=from_phone,
                to_phone=to_phone,
                body=text,
            )
            self.repo.create_message(message)

            self.crm.add_interaction(customer_id=customer.id, type="whatsapp", content=text)
            self.repo.mark_webhook_event_status(
                tenant_id=account.tenant_id,
                provider=provider,
                external_event_id=external_event_id,
                status="processed",
            )

            reply = None
            try:
                reply = self._maybe_bot_reply(
                    tenant_id=account.tenant_id,
                    customer_id=customer.id,
                    conversation=conversation,
                    inbound_text=text,
                    from_phone=from_phone,
                    phone_number_id=phone_number_id,
                    to_phone=to_phone,
                    inbound_provider_message_id=provider_message_id,
                )
            except Exception as err:
                log_event(
                    "assistant_whatsapp_bot_reply_failed",
                    level="warning",
                    tenant_id=account.tenant_id,
                    provider=provider,
                    error=str(err),
                )

            log_event(
                "messaging_whatsapp_inbound_processed",
                tenant_id=account.tenant_id,
                provider=provider,
                duration_ms=int(timer.seconds() * 1000),
                replied=bool(reply),
            )
            return {
                "status": "processed",
                "tenant_id": account.tenant_id,
                "message_id": provider_message_id,
                "replied": bool(reply),
            }
        finally:
            clear_tenant_id()

    def _maybe_bot_reply(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        conversation: Conversation,
        inbound_text: str,
        from_phone: str,
        phone_number_id: str,
        to_phone: str | None,
        inbound_provider_message_id: str,
    ) -> str | None:
        cfg = get_config()
        if not cfg.CHATBOT_SERVICE_BASE_URL:
            return None
        if not cfg.WHATSAPP_CLOUD_ACCESS_TOKEN:
            return None

        trace_id = str(uuid.uuid4())
        chatbot_client_id = (getattr(cfg, "CHATBOT_CLIENT_ID", None) or "").strip() or tenant_id

        upstream_payload = {
            "client_id": chatbot_client_id,
            "conversation_id": conversation.id,
            "session_id": conversation.assistant_session_id,
            "message": inbound_text,
            "surface": "whatsapp",
            # `chatbot1` expects a UUID-like user id; use customer id for stable scoping.
            "user_id": customer_id,
            "tenant_id": tenant_id,
            "customer_id": customer_id,
        }

        raw = ChatbotClient().send_message(payload=upstream_payload, trace_id=trace_id)
        chatbot_session_id = raw.get("session_id") if isinstance(raw.get("session_id"), str) else conversation.assistant_session_id
        if chatbot_session_id and chatbot_session_id != conversation.assistant_session_id:
            self.repo.upsert_conversation(conversation.with_assistant_session(chatbot_session_id).touch(datetime.now(timezone.utc)))

        normalized = normalize_chatbot_response(raw, conversation_id=conversation.id, chatbot_session_id=chatbot_session_id)
        reply_text = (normalized.get("reply", {}) or {}).get("text")
        if not isinstance(reply_text, str) or not reply_text.strip():
            return None
        reply_text = reply_text.strip()

        # Best-effort outbound send + persistence.
        from core.db.session import db_session  # local import to avoid cycles

        tenant_uuid = uuid.UUID(tenant_id)
        customer_uuid = uuid.UUID(customer_id)
        conversation_uuid = uuid.UUID(conversation.id)

        idempotency_key = f"auto:assistant_whatsapp_reply:{inbound_provider_message_id}"
        now = datetime.now(timezone.utc)

        with db_session() as session:
            outbound = OutboundRepo(session)
            existing = outbound.get_by_idempotency_key(tenant_id=tenant_uuid, idempotency_key=idempotency_key)
            if existing is not None and (existing.status or "").strip().lower() != "failed":
                return reply_text

            msg = outbound.create_message(
                tenant_id=tenant_uuid,
                customer_id=customer_uuid,
                appointment_id=None,
                template_id=None,
                type="assistant_whatsapp_reply",
                channel="whatsapp",
                rendered_body=reply_text,
                status="pending",
                error_message=None,
                sent_by_user_id=None,
                sent_at=None,
                recipient=None,
                delivery_status="queued",
                delivery_status_updated_at=now,
                error_code=None,
                idempotency_key=idempotency_key,
                trigger_type="assistant_whatsapp_inbound",
                trace_id=trace_id,
                conversation_id=conversation_uuid,
                assistant_session_id=chatbot_session_id,
            )

            to_phone_digits = _normalize_phone_for_wa(from_phone)
            if to_phone_digits is None:
                outbound.mark_failed(tenant_id=tenant_uuid, message_id=str(msg.id), error_message="customer_missing_valid_phone")
                msg.error_code = "missing_recipient"
                session.add(msg)
                session.flush()
                inc_counter("outbound_send_total", labels={"status": "failed", "channel": "whatsapp", "type": msg.type})
                return None

            provider = MetaWhatsAppCloudProvider()
            try:
                res = provider.send_whatsapp_text(
                    phone_number_id=phone_number_id,
                    to_phone=to_phone_digits,
                    body=reply_text,
                    trace_id=trace_id,
                    idempotency_key=idempotency_key,
                )
                msg.provider = res.provider
                msg.provider_message_id = res.provider_message_id
                msg.recipient = to_phone_digits
                msg.delivery_status = "accepted"
                msg.delivery_status_updated_at = now
                msg.status = "sent"
                msg.sent_at = now
                session.add(msg)
                session.flush()
                inc_counter("outbound_send_total", labels={"status": "sent", "channel": "whatsapp", "type": msg.type})
            except Exception as err:
                outbound.mark_failed(tenant_id=tenant_uuid, message_id=str(msg.id), error_message=str(err))
                msg.error_code = "provider_send_failed"
                session.add(msg)
                session.flush()
                inc_counter("outbound_send_total", labels={"status": "failed", "channel": "whatsapp", "type": msg.type})
                return None

        # Operational visibility.
        try:
            self.crm.add_interaction(customer_id=customer_id, type="assistant_whatsapp_reply", content=reply_text)
        except Exception:
            log_event(
                "assistant_whatsapp_reply_interaction_failed",
                level="warning",
                tenant_id=tenant_id,
                trace_id=trace_id,
                conversation_id=conversation.id,
            )
        return reply_text


def _normalize_phone_for_wa(value: str) -> str | None:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if not digits:
        return None
    # Minimal sanity check; WhatsApp E.164 digits typically 8..15.
    if len(digits) < 8 or len(digits) > 15:
        return None
    return digits
