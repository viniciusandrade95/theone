"""add services and appointments

Revision ID: f7c342e16bec
Revises: 347b45647e1f
Create Date: 2026-02-06 18:43:42.432960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f7c342e16bec'
down_revision: Union[str, Sequence[str], None] = '347b45647e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # SERVICES
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # APPOINTMENTS
    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), server_default="booked", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Helpful indexes
    op.create_index("ix_services_tenant_name", "services", ["tenant_id", "name"])
    op.create_index("ix_appointments_tenant_starts", "appointments", ["tenant_id", "starts_at"])
    op.create_index("ix_appointments_customer", "appointments", ["tenant_id", "customer_id"])

    # -------------------------
    # RLS (match your existing pattern)
    # -------------------------
    op.execute("ALTER TABLE services ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;")

    # Policy assumes you are using current_setting('app.current_tenant_id', true)
    # and setting it via SET LOCAL in your db_session() context.
    op.execute("""
    CREATE POLICY services_tenant_isolation
    ON services
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """)

    op.execute("""
    CREATE POLICY appointments_tenant_isolation
    ON appointments
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    """)


def downgrade():
    op.execute("DROP POLICY IF EXISTS appointments_tenant_isolation ON appointments;")
    op.execute("DROP POLICY IF EXISTS services_tenant_isolation ON services;")

    op.drop_index("ix_appointments_customer", table_name="appointments")
    op.drop_index("ix_appointments_tenant_starts", table_name="appointments")
    op.drop_index("ix_services_tenant_name", table_name="services")

    op.drop_table("appointments")
    op.drop_table("services")
