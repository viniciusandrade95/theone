"""add booking settings and online booking flags

Revision ID: a8c3f1d2b7c1
Revises: e1f8c4ab92de
Create Date: 2026-04-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a8c3f1d2b7c1"
down_revision: Union[str, Sequence[str], None] = "e1f8c4ab92de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def _uuid_type():
    if _is_postgres():
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def upgrade() -> None:
    op.create_table(
        "booking_settings",
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("booking_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("booking_slug", sa.String(length=80), nullable=True),
        sa.Column("public_business_name", sa.String(length=255), nullable=True),
        sa.Column("public_contact_phone", sa.String(length=40), nullable=True),
        sa.Column("public_contact_email", sa.String(length=255), nullable=True),
        sa.Column("min_booking_notice_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_booking_notice_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("auto_confirm_bookings", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ux_booking_settings_slug", "booking_settings", ["booking_slug"], unique=True)

    op.add_column("services", sa.Column("is_bookable_online", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_services_tenant_bookable_online", "services", ["tenant_id", "is_bookable_online"])

    op.add_column("appointments", sa.Column("needs_confirmation", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_appointments_tenant_needs_confirmation", "appointments", ["tenant_id", "needs_confirmation"])


def downgrade() -> None:
    op.drop_index("ix_appointments_tenant_needs_confirmation", table_name="appointments")
    op.drop_column("appointments", "needs_confirmation")

    op.drop_index("ix_services_tenant_bookable_online", table_name="services")
    op.drop_column("services", "is_bookable_online")

    op.drop_index("ux_booking_settings_slug", table_name="booking_settings")
    op.drop_table("booking_settings")

