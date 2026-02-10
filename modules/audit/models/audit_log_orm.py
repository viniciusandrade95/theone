import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from core.db.base import Base


class AuditLogORM(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_tenant_created_at", "tenant_id", "created_at"),
        Index("ix_audit_log_tenant_entity", "tenant_id", "entity_type", "entity_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(32), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    before = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    after = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
