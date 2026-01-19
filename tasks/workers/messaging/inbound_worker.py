from core.tenancy import set_tenant_id, clear_tenant_id
from core.events import MessageReceived
from modules.messaging.service import InboundMessagingService
from modules.billing.service import BillingService, Feature, assert_allowed


class InboundMessageWorker:
    def __init__(self, inbound_service: InboundMessagingService, billing: BillingService):
        self.inbound_service = inbound_service
        self.billing = billing

    def handle(self, event: MessageReceived) -> dict:
        clear_tenant_id()
        set_tenant_id(event.tenant_id)
        try:
            # Gate: WhatsApp premium
            assert_allowed(self.billing.can_use_feature(Feature.WHATSAPP))
            return self.inbound_service.handle_inbound(event.payload)
        finally:
            clear_tenant_id()
