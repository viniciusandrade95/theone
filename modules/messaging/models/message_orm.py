import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base
from modules.messaging.models.message import Message


class MessageORM(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_message_id", name="uq_messages_tenant_provider_message"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    direction = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    provider_message_id = Column(String, nullable=False)
    from_phone = Column(String, nullable=False)
    to_phone = Column(String, nullable=True)
    body = Column(String, nullable=False)
    status = Column(String, nullable=False, default="received")
    received_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_domain(self) -> Message:
        return Message(
            id=str(self.id),
            tenant_id=str(self.tenant_id),
            conversation_id=str(self.conversation_id),
            direction=self.direction,
            provider=self.provider,
            provider_message_id=self.provider_message_id,
            from_phone=self.from_phone,
            to_phone=self.to_phone,
            body=self.body,
            status=self.status,
            received_at=self.received_at,
            sent_at=self.sent_at,
            created_at=self.created_at,
        )
