from modules.messaging.service import InboundWebhookService


def process_inbound_webhook(*, inbound_service: InboundWebhookService, payload: dict, signature_valid: bool) -> dict:
    return inbound_service.handle_inbound(payload=payload, signature_valid=signature_valid)
