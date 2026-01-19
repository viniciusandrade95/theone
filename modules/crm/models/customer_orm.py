from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, DateTime, JSON, String
from core.db.base import Base
from datetime import datetime
from modules.crm.models.customer import Customer
from modules.crm.models.pipeline import PipelineStage


class CustomerORM(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)

    name: Mapped[str] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    consent_marketing: Mapped[bool] = mapped_column(Boolean, default=False)
    stage: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(DateTime)

    def to_domain(self) -> Customer:
        return Customer(
            id=self.id,
            tenant_id=self.tenant_id,
            name=self.name,
            phone=self.phone,
            email=self.email,
            tags=frozenset(self.tags or []),
            consent_marketing=self.consent_marketing,
            stage=PipelineStage(self.stage),
            created_at=self.created_at,
        )

    @staticmethod
    def from_domain(customer: Customer) -> "CustomerORM":
        return CustomerORM(
            id=customer.id,
            tenant_id=customer.tenant_id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email,
            tags=list(customer.tags),
            consent_marketing=customer.consent_marketing,
            stage=customer.stage.value,
            created_at=customer.created_at,
        )
