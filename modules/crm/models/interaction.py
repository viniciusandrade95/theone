from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Interaction:
    id: str
    tenant_id: str
    customer_id: str
    type: str  # "note" | "whatsapp" | etc (string por agora)
    content: str
    created_at: datetime

    @staticmethod
    def create(*, interaction_id: str, tenant_id: str, customer_id: str, type: str, content: str) -> "Interaction":
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not interaction_id or interaction_id.strip() == "":
            raise ValidationError("interaction_id is required")
        if not customer_id or customer_id.strip() == "":
            raise ValidationError("customer_id is required")
        if not type or type.strip() == "":
            raise ValidationError("type is required")
        if not content or content.strip() == "":
            raise ValidationError("content is required")

        return Interaction(
            id=interaction_id.strip(),
            tenant_id=tenant_id.strip(),
            customer_id=customer_id.strip(),
            type=type.strip().lower(),
            content=content.strip(),
            created_at=_now(),
        )
