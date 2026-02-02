import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func

from core.db.base import Base
from modules.crm.models.customer import Customer
from modules.crm.models.pipeline import PipelineStage


class CustomerORM(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index(
            "uq_customers_tenant_phone",
            "tenant_id",
            "phone",
            unique=True,
            postgresql_where=text("phone IS NOT NULL"),
        ),
        Index(
            "uq_customers_tenant_email",
            "tenant_id",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
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
