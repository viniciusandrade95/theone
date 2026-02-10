from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class TenantSettingsORM(Base):
    __tablename__ = "tenant_settings"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    business_name = Column(String(255), nullable=True)
    default_timezone = Column(String(120), nullable=False, server_default="UTC")
    currency = Column(String(12), nullable=False, server_default="USD")
    calendar_default_view = Column(String(16), nullable=False, server_default="week")
    default_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    primary_color = Column(String(32), nullable=True)
    logo_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
