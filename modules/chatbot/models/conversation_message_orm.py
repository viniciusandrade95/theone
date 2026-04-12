import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from core.db.base import Base


class ChatbotConversationMessageORM(Base):
    __tablename__ = "chatbot_conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chatbot_conversation_sessions.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    surface = Column(String(length=64), nullable=False, server_default="dashboard")
    role = Column(String(length=16), nullable=False)  # user|assistant|system
    content = Column(Text, nullable=False)

    intent = Column(String(length=80), nullable=True)
    epoch = Column(Integer, nullable=False, server_default="0")
    meta = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

