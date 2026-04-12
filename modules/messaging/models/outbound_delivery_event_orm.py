import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from core.db.base import Base


class OutboundDeliveryEventORM(Base):
    __tablename__ = "outbound_delivery_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "external_event_id", name="uq_outbound_delivery_tenant_provider_event"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(32), nullable=False)
    external_event_id = Column(String(255), nullable=False)

    provider_message_id = Column(String(255), nullable=True, index=True)
    channel = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

