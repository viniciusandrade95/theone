import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class AssistantHandoffORM(Base):
    __tablename__ = "assistant_handoffs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "conversation_id", "conversation_epoch", name="uq_assistant_handoff_conversation_epoch"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_epoch = Column(Integer, nullable=False, server_default="0")

    surface = Column(String(length=64), nullable=False, server_default="dashboard")
    session_id = Column(String(length=255), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(String(length=32), nullable=False, server_default="open")  # open|claimed|closed
    reason = Column(String(length=255), nullable=True)
    summary = Column(Text, nullable=True)

    claimed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

