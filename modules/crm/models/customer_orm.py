import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func

from core.db.base import Base
from modules.crm.models.customer import Customer
from modules.crm.models.pipeline import PipelineStage


class CustomerORM(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "phone", name="uq_customers_tenant_phone"),
        UniqueConstraint("tenant_id", "email", name="uq_customers_tenant_email"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    tags = Column(ARRAY(String), nullable=False, default=list)

    consent_marketing = Column(Boolean, nullable=False, default=False)

    stage = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_domain(self) -> Customer:
        return Customer(
            id=str(self.id),
            tenant_id=str(self.tenant_id),
            name=self.name,
            phone=self.phone,
            email=self.email,
            tags=frozenset(self.tags or []),
            consent_marketing=self.consent_marketing,
            stage=PipelineStage(self.stage),
            created_at=self.created_at,
        )
