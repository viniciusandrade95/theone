from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class User:
    id: str
    tenant_id: str
    email: str
    password_hash: str
    created_at: datetime

    @staticmethod
    def create(*, user_id: str, tenant_id: str, email: str, password_hash: str) -> "User":
        if not user_id or user_id.strip() == "":
            raise ValidationError("user_id is required")
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not email or email.strip() == "" or "@" not in email:
            raise ValidationError("valid email is required")
        if not password_hash or password_hash.strip() == "":
            raise ValidationError("password_hash is required")

        return User(
            id=user_id.strip(),
            tenant_id=tenant_id.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            created_at=_now(),
        )
