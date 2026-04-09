from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class BookingSettingsORM(Base):
    __tablename__ = "booking_settings"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )

    booking_enabled = Column(Boolean, nullable=False, server_default="false")
    booking_slug = Column(String(80), nullable=True, unique=True)

    public_business_name = Column(String(255), nullable=True)
    public_contact_phone = Column(String(40), nullable=True)
    public_contact_email = Column(String(255), nullable=True)

    min_booking_notice_minutes = Column(Integer, nullable=False, server_default="60")
    max_booking_notice_days = Column(Integer, nullable=False, server_default="90")
    auto_confirm_bookings = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

