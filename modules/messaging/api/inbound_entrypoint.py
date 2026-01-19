from core.events import EventBus, MessageReceived
from core.tenancy import require_tenant_id


def accept_inbound_webhook(payload: dict, bus: EventBus) -> dict:
    tenant_id = require_tenant_id()
    bus.publish(MessageReceived(tenant_id=tenant_id, payload=payload))
    return {"status": "accepted"}
