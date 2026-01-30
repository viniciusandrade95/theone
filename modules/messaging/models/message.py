from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Message:
    id: str
    tenant_id: str
    conversation_id: str
    direction: str
    provider: str
    provider_message_id: str
    from_phone: str
    to_phone: str | None
    body: str
    status: str
    received_at: datetime | None
    sent_at: datetime | None
    created_at: datetime

    @staticmethod
    def inbound(
        *,
        message_id: str,
        tenant_id: str,
        conversation_id: str,
        provider: str,
        provider_message_id: str,
        from_phone: str,
        to_phone: str | None,
        body: str,
        received_at: datetime | None = None,
    ) -> "Message":
        if not message_id or message_id.strip() == "":
            raise ValidationError("message_id is required")
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not conversation_id or conversation_id.strip() == "":
            raise ValidationError("conversation_id is required")
        if not provider or provider.strip() == "":
            raise ValidationError("provider is required")
        if not provider_message_id or provider_message_id.strip() == "":
            raise ValidationError("provider_message_id is required")
        if not from_phone or from_phone.strip() == "":
            raise ValidationError("from_phone is required")
        if not body or body.strip() == "":
            raise ValidationError("body is required")

        now = _now()
        return Message(
            id=message_id.strip(),
            tenant_id=tenant_id.strip(),
            conversation_id=conversation_id.strip(),
            direction="inbound",
            provider=provider.strip().lower(),
            provider_message_id=provider_message_id.strip(),
            from_phone=from_phone.strip(),
            to_phone=to_phone.strip() if to_phone and to_phone.strip() != "" else None,
            body=body.strip(),
            status="received",
            received_at=received_at or now,
            sent_at=None,
            created_at=now,
        )
