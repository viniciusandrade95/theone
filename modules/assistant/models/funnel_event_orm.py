import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class AssistantFunnelEventORM(Base):
    __tablename__ = "assistant_funnel_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "dedupe_key", name="uq_assistant_funnel_events_tenant_dedupe_key"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    trace_id = Column(String(128), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    assistant_session_id = Column(String(255), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)

    event_name = Column(String(64), nullable=False, index=True)
    event_source = Column(String(32), nullable=False, server_default="theone")
    channel = Column(String(32), nullable=True, index=True)

    related_entity_type = Column(String(64), nullable=True, index=True)
    related_entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    dedupe_key = Column(String(255), nullable=True)
    meta = Column("metadata", JSON, nullable=False, server_default="{}")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
