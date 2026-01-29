import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from core.db.base import Base
from modules.crm.models.interaction import Interaction


class InteractionORM(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )

    type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_domain(self) -> Interaction:
        content = ""
        if isinstance(self.payload, dict):
            content = str(self.payload.get("content", ""))
        elif self.payload is not None:
            content = str(self.payload)
        return Interaction(
            id=str(self.id),
            tenant_id=str(self.tenant_id),
            customer_id=str(self.customer_id),
            type=self.type,
            content=content,
            created_at=self.created_at,
        )
