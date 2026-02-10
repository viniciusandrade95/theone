import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from core.db.base import Base


class AppointmentORM(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)

    status = Column(String, nullable=False, server_default="booked")
    cancelled_reason = Column(Text, nullable=True)
    status_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
