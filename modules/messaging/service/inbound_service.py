from core.errors import NotFoundError
from core.tenancy import require_tenant_id
from modules.messaging.models import InboundMessage
from modules.crm.service import CrmService


class InboundMessagingService:
    def __init__(self, crm: CrmService):
        self.crm = crm

    def handle_inbound(self, payload: dict):
        _ = require_tenant_id()  # garante contexto

        msg = InboundMessage.parse(payload)

        customer = self.crm.find_customer_by_phone(phone=msg.from_phone)
        if customer is None:
            # nesta V1: se não existir customer, falha (depois fazemos auto-create)
            raise NotFoundError("Customer not found for inbound message", meta={"phone": msg.from_phone})

        self.crm.add_interaction(
            customer_id=customer.id,
            type="whatsapp",
            content=msg.text,
        )

        return {"status": "ok", "customer_id": customer.id, "message_id": msg.message_id}
