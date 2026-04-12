"""add assistant handoffs

Revision ID: 7c1e2a9b4d3f
Revises: 5a9c2d1e8f0a
Create Date: 2026-04-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7c1e2a9b4d3f"
down_revision: Union[str, Sequence[str], None] = "5a9c2d1e8f0a"
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
        "assistant_handoffs",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conversation_id", _uuid_type(), nullable=False),
        sa.Column("conversation_epoch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("surface", sa.String(length=64), nullable=False, server_default="dashboard"),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("user_id", _uuid_type(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("customer_id", _uuid_type(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("claimed_by_user_id", _uuid_type(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "conversation_id", "conversation_epoch", name="uq_assistant_handoff_conversation_epoch"),
    )
    op.create_index("ix_assistant_handoffs_tenant_id", "assistant_handoffs", ["tenant_id"])
    op.create_index("ix_assistant_handoffs_conversation_id", "assistant_handoffs", ["conversation_id"])
    op.create_index("ix_assistant_handoffs_user_id", "assistant_handoffs", ["user_id"])
    op.create_index("ix_assistant_handoffs_customer_id", "assistant_handoffs", ["customer_id"])

    if _is_postgres():
        op.execute("ALTER TABLE assistant_handoffs ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_assistant_handoffs
            ON assistant_handoffs
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_assistant_handoffs ON assistant_handoffs")

    op.drop_index("ix_assistant_handoffs_customer_id", table_name="assistant_handoffs")
    op.drop_index("ix_assistant_handoffs_user_id", table_name="assistant_handoffs")
    op.drop_index("ix_assistant_handoffs_conversation_id", table_name="assistant_handoffs")
    op.drop_index("ix_assistant_handoffs_tenant_id", table_name="assistant_handoffs")
    op.drop_table("assistant_handoffs")

