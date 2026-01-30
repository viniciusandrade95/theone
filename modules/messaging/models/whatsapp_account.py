from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class WhatsAppAccount:
    id: str
    tenant_id: str
    provider: str
    phone_number_id: str
    status: str
    created_at: datetime

    @staticmethod
    def create(*, account_id: str, tenant_id: str, provider: str, phone_number_id: str, status: str = "active") -> "WhatsAppAccount":
        if not account_id or account_id.strip() == "":
            raise ValidationError("account_id is required")
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not provider or provider.strip() == "":
            raise ValidationError("provider is required")
        if not phone_number_id or phone_number_id.strip() == "":
            raise ValidationError("phone_number_id is required")

        return WhatsAppAccount(
            id=account_id.strip(),
            tenant_id=tenant_id.strip(),
            provider=provider.strip().lower(),
            phone_number_id=phone_number_id.strip(),
            status=status.strip().lower(),
            created_at=_now(),
        )
