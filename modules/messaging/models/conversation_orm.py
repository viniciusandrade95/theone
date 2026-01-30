import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base
from modules.messaging.models.conversation import Conversation


class ConversationORM(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "customer_id", "channel", name="uq_conversations_tenant_customer_channel"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String, nullable=False)
    state = Column(String, nullable=False, default="open")
    last_message_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def to_domain(self) -> Conversation:
        return Conversation(
            id=str(self.id),
            tenant_id=str(self.tenant_id),
            customer_id=str(self.customer_id),
            channel=self.channel,
            state=self.state,
            last_message_at=self.last_message_at,
        )
