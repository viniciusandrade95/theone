from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Conversation:
    id: str
    tenant_id: str
    customer_id: str
    channel: str
    state: str
    last_message_at: datetime

    @staticmethod
    def create(
        *,
        conversation_id: str,
        tenant_id: str,
        customer_id: str,
        channel: str,
        state: str = "open",
        last_message_at: datetime | None = None,
    ) -> "Conversation":
        if not conversation_id or conversation_id.strip() == "":
            raise ValidationError("conversation_id is required")
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not customer_id or customer_id.strip() == "":
            raise ValidationError("customer_id is required")
        if not channel or channel.strip() == "":
            raise ValidationError("channel is required")

        return Conversation(
            id=conversation_id.strip(),
            tenant_id=tenant_id.strip(),
            customer_id=customer_id.strip(),
            channel=channel.strip().lower(),
            state=state.strip().lower(),
            last_message_at=last_message_at or _now(),
        )

    def touch(self, when: datetime | None = None) -> "Conversation":
        return Conversation(
            id=self.id,
            tenant_id=self.tenant_id,
            customer_id=self.customer_id,
            channel=self.channel,
            state=self.state,
            last_message_at=when or _now(),
        )
