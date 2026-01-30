from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class WebhookEvent:
    id: str
    tenant_id: str
    provider: str
    external_event_id: str
    payload: dict
    signature_valid: bool
    status: str
    received_at: datetime
    processed_at: datetime | None

    @staticmethod
    def create(
        *,
        event_id: str,
        tenant_id: str,
        provider: str,
        external_event_id: str,
        payload: dict,
        signature_valid: bool,
        status: str = "received",
    ) -> "WebhookEvent":
        if not event_id or event_id.strip() == "":
            raise ValidationError("event_id is required")
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not provider or provider.strip() == "":
            raise ValidationError("provider is required")
        if not external_event_id or external_event_id.strip() == "":
            raise ValidationError("external_event_id is required")
        if payload is None:
            raise ValidationError("payload is required")

        return WebhookEvent(
            id=event_id.strip(),
            tenant_id=tenant_id.strip(),
            provider=provider.strip().lower(),
            external_event_id=external_event_id.strip(),
            payload=payload,
            signature_valid=bool(signature_valid),
            status=status.strip().lower(),
            received_at=_now(),
            processed_at=None,
        )
