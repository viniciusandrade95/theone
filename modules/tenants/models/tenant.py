from dataclasses import dataclass
from core.errors import ValidationError


@dataclass(frozen=True)
class Tenant:
    id: str
    name: str

    @staticmethod
    def create(*, tenant_id: str, name: str) -> "Tenant":
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not name or name.strip() == "":
            raise ValidationError("name is required")

        return Tenant(
            id=tenant_id.strip(),
            name=name.strip(),
        )
