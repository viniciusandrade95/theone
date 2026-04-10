"""add assistant prebook requests

Revision ID: 3a1b2c3d4e5f
Revises: 2f9a7b1c3d4e
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "2f9a7b1c3d4e"
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
        "assistant_prebook_requests",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("conversation_id", _uuid_type(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("trace_id", sa.String(length=255), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=True),
        sa.Column("actor_id", _uuid_type(), nullable=True),
        sa.Column("customer_id", _uuid_type(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("service_id", _uuid_type(), sa.ForeignKey("services.id", ondelete="SET NULL"), nullable=True),
        sa.Column("location_id", _uuid_type(), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("appointment_id", _uuid_type(), sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="started"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_assistant_prebook_tenant_key"),
    )
    op.create_index("ix_assistant_prebook_requests_tenant_id", "assistant_prebook_requests", ["tenant_id"])
    op.create_index("ix_assistant_prebook_requests_conversation_id", "assistant_prebook_requests", ["conversation_id"])
    op.create_index("ix_assistant_prebook_requests_customer_id", "assistant_prebook_requests", ["customer_id"])
    op.create_index("ix_assistant_prebook_requests_service_id", "assistant_prebook_requests", ["service_id"])
    op.create_index("ix_assistant_prebook_requests_location_id", "assistant_prebook_requests", ["location_id"])
    op.create_index("ix_assistant_prebook_requests_appointment_id", "assistant_prebook_requests", ["appointment_id"])

    if _is_postgres():
        op.execute("ALTER TABLE assistant_prebook_requests ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_assistant_prebook_requests
            ON assistant_prebook_requests
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_assistant_prebook_requests ON assistant_prebook_requests")

    op.drop_index("ix_assistant_prebook_requests_appointment_id", table_name="assistant_prebook_requests")
    op.drop_index("ix_assistant_prebook_requests_location_id", table_name="assistant_prebook_requests")
    op.drop_index("ix_assistant_prebook_requests_service_id", table_name="assistant_prebook_requests")
    op.drop_index("ix_assistant_prebook_requests_customer_id", table_name="assistant_prebook_requests")
    op.drop_index("ix_assistant_prebook_requests_conversation_id", table_name="assistant_prebook_requests")
    op.drop_index("ix_assistant_prebook_requests_tenant_id", table_name="assistant_prebook_requests")
    op.drop_table("assistant_prebook_requests")

