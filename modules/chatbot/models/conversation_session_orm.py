import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class ChatbotConversationSessionORM(Base):
    __tablename__ = "chatbot_conversation_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "surface", name="uq_chatbot_tenant_user_surface"),
    )

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)

    client_id = Column(String(length=80), nullable=False)
    chatbot_session_id = Column(String(length=255), nullable=True)
    surface = Column(String(length=64), nullable=False, server_default="dashboard")
    status = Column(String(length=32), nullable=False, server_default="active")
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)
