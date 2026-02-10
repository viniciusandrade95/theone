import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class LocationORM(Base):
    __tablename__ = "locations"
    __table_args__ = (
        Index("ix_locations_tenant_active", "tenant_id", "is_active"),
        Index("ix_locations_tenant_name", "tenant_id", "name"),
        Index("ix_locations_tenant_deleted", "tenant_id", "deleted_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(120), nullable=False)
    timezone = Column(String(120), nullable=False)

    address_line1 = Column(Text, nullable=True)
    address_line2 = Column(Text, nullable=True)
    city = Column(String(120), nullable=True)
    postcode = Column(String(40), nullable=True)
    country = Column(String(120), nullable=True)
    phone = Column(String(40), nullable=True)
    email = Column(String(255), nullable=True)

    is_active = Column(Boolean, nullable=False, server_default="true")
    hours_json = Column(JSON, nullable=True)
    allow_overlaps = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
