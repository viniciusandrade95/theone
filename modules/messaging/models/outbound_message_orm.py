import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class OutboundMessageORM(Base):
    __tablename__ = "outbound_messages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbound_messages_tenant_idempotency_key"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("message_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    type = Column(String(64), nullable=False, index=True)
    channel = Column(String(32), nullable=False)
    rendered_body = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, server_default="pending", index=True)
    error_message = Column(Text, nullable=True)
    sent_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Provider-backed lifecycle (v2)
    provider = Column(String(32), nullable=True, index=True)
    provider_message_id = Column(String(255), nullable=True, index=True)
    recipient = Column(String(255), nullable=True)
    delivery_status = Column(String(32), nullable=True, index=True)
    delivery_status_updated_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(64), nullable=True)
    idempotency_key = Column(String(255), nullable=True)
    trigger_type = Column(String(32), nullable=True)
    trace_id = Column(String(128), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    assistant_session_id = Column(String(255), nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
