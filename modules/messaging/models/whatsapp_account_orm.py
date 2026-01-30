import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base
from modules.messaging.models.whatsapp_account import WhatsAppAccount


class WhatsAppAccountORM(Base):
    __tablename__ = "whatsapp_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "phone_number_id", name="uq_whatsapp_accounts_provider_phone"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    phone_number_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_domain(self) -> WhatsAppAccount:
        return WhatsAppAccount(
            id=str(self.id),
            tenant_id=str(self.tenant_id),
            provider=self.provider,
            phone_number_id=self.phone_number_id,
            status=self.status,
            created_at=self.created_at,
        )
