import uuid
from core.errors import NotFoundError, ForbiddenError
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.messaging.models import WebhookEvent, Conversation, Message
from modules.messaging.repo.messaging_repo import MessagingRepo
from modules.crm.service import CrmService
from modules.billing.service import BillingService, Feature, assert_allowed


class InboundWebhookService:
    def __init__(self, repo: MessagingRepo, crm: CrmService, billing: BillingService):
        self.repo = repo
        self.crm = crm
        self.billing = billing

    def handle_inbound(self, *, payload: dict, signature_valid: bool) -> dict:
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

            return {
                "status": "processed",
                "tenant_id": account.tenant_id,
                "message_id": provider_message_id,
            }
        finally:
            clear_tenant_id()
