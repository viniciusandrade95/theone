import uuid
from sqlalchemy import Boolean, Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class ServiceORM(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False)
    price_cents = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
