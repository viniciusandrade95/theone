from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Tenant:
    id: str
    name: str
    created_at: datetime

    @staticmethod
    def create(tenant_id: str, name: str) -> "Tenant":
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not name or name.strip() == "":
            raise ValidationError("name is required")

        return Tenant(
            id=tenant_id.strip(),
            name=name.strip(),
            created_at=_now(),
        )
