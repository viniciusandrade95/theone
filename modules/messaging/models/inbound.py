from dataclasses import dataclass
from core.errors import ValidationError


@dataclass(frozen=True)
class InboundMessage:
    message_id: str
    from_phone: str
    text: str

    @staticmethod
    def parse(payload: dict) -> "InboundMessage":
        # payload mínimo esperado (framework-agnostic)
        message_id = (payload.get("message_id") or "").strip()
        from_phone = (payload.get("from_phone") or "").strip()
        text = (payload.get("text") or "").strip()

        if not message_id:
            raise ValidationError("message_id is required")
        if not from_phone:
            raise ValidationError("from_phone is required")
        if not text:
            raise ValidationError("text is required")

        # normalização simples
        from_phone = from_phone.replace(" ", "")
        return InboundMessage(message_id=message_id, from_phone=from_phone, text=text)
