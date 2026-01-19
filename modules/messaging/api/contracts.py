from dataclasses import dataclass

@dataclass(frozen=True)
class InboundWebhookPayload:
    message_id: str
    from_phone: str
    text: str
