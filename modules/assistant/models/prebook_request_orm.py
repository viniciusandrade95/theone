import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class AssistantPrebookRequestORM(Base):
    __tablename__ = "assistant_prebook_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_assistant_prebook_tenant_key"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key = Column(String(length=255), nullable=False)

    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(String(length=255), nullable=True)
    trace_id = Column(String(length=255), nullable=True)

    actor_type = Column(String(length=32), nullable=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True)

    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)

    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = Column(String(length=32), nullable=False, server_default="started")
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

