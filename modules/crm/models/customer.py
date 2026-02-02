from dataclasses import dataclass
from datetime import datetime, timezone
from core.errors import ValidationError
from modules.crm.models.pipeline import PipelineStage


def _now():
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Customer:
    id: str
    tenant_id: str
    name: str
    phone: str | None
    email: str | None
    tags: frozenset[str]
    consent_marketing: bool
    stage: PipelineStage
    created_at: datetime

    @staticmethod
    def create(
        *,
        customer_id: str,
        tenant_id: str,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        tags: set[str] | None = None,
        consent_marketing: bool = False,
        stage: PipelineStage = PipelineStage.LEAD,
    ) -> "Customer":
        if not tenant_id or tenant_id.strip() == "":
            raise ValidationError("tenant_id is required")
        if not customer_id or customer_id.strip() == "":
            raise ValidationError("customer_id is required")
        if not name or name.strip() == "":
            raise ValidationError("name is required")

        if email is not None and email.strip() != "" and "@" not in email:
            raise ValidationError("email must be valid")

        clean_tags = frozenset((t.strip().lower() for t in (tags or set()) if t.strip() != ""))

        return Customer(
            id=customer_id.strip(),
            tenant_id=tenant_id.strip(),
            name=name.strip(),
            phone=phone.strip() if phone and phone.strip() != "" else None,
            email=email.strip().lower() if email and email.strip() != "" else None,
            tags=clean_tags,
            consent_marketing=bool(consent_marketing),
            stage=stage,
            created_at=_now(),
        )

    def with_tags(self, tags: set[str]) -> "Customer":
        clean_tags = frozenset((t.strip().lower() for t in tags if t.strip() != ""))
        return Customer(
            id=self.id,
            tenant_id=self.tenant_id,
            name=self.name,
            phone=self.phone,
            email=self.email,
            tags=clean_tags,
            consent_marketing=self.consent_marketing,
            stage=self.stage,
            created_at=self.created_at,
        )

    def with_stage(self, stage: PipelineStage) -> "Customer":
        return Customer(
            id=self.id,
            tenant_id=self.tenant_id,
            name=self.name,
            phone=self.phone,
            email=self.email,
            tags=self.tags,
            consent_marketing=self.consent_marketing,
            stage=stage,
            created_at=self.created_at,
        )

    def with_updates(
        self,
        *,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        tags: set[str] | None = None,
        consent_marketing: bool | None = None,
    ) -> "Customer":
        new_name = self.name if name is None else name
        if not new_name or new_name.strip() == "":
            raise ValidationError("name is required")

        new_email = self.email if email is None else email
        if new_email is not None and new_email.strip() != "" and "@" not in new_email:
            raise ValidationError("email must be valid")

        new_tags = self.tags if tags is None else frozenset((t.strip().lower() for t in tags if t.strip() != ""))

        return Customer(
            id=self.id,
            tenant_id=self.tenant_id,
            name=new_name.strip(),
            phone=phone.strip() if phone and phone.strip() != "" else (self.phone if phone is None else None),
            email=new_email.strip().lower() if new_email and new_email.strip() != "" else (None if new_email is not None else self.email),
            tags=new_tags,
            consent_marketing=self.consent_marketing if consent_marketing is None else bool(consent_marketing),
            stage=self.stage,
            created_at=self.created_at,
        )
