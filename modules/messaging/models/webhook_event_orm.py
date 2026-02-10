import uuid
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from core.db.base import Base
from modules.messaging.models.webhook_event import WebhookEvent


class WebhookEventORM(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "external_event_id", name="uq_webhook_events_tenant_provider_external"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    external_event_id = Column(String, nullable=False)
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    signature_valid = Column(Boolean, nullable=False)
    status = Column(String, nullable=False, default="received")
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> WebhookEvent:
        return WebhookEvent(
            id=str(self.id),
            tenant_id=str(self.tenant_id),
            provider=self.provider,
            external_event_id=self.external_event_id,
            payload=self.payload,
            signature_valid=self.signature_valid,
            status=self.status,
            received_at=self.received_at,
            processed_at=self.processed_at,
        )
