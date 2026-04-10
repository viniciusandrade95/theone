"""add chatbot conversation sessions

Revision ID: 1d2c3e4f5a6b
Revises: f7c342e16bec
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "1d2c3e4f5a6b"
down_revision: Union[str, Sequence[str], None] = "f7c342e16bec"
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
        "chatbot_conversation_sessions",
        sa.Column("conversation_id", _uuid_type(), primary_key=True),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", _uuid_type(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", _uuid_type(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("client_id", sa.String(length=80), nullable=False),
        sa.Column("chatbot_session_id", sa.String(length=255), nullable=True),
        sa.Column("surface", sa.String(length=64), nullable=False, server_default="dashboard"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "user_id", "surface", name="uq_chatbot_tenant_user_surface"),
    )
    op.create_index("ix_chatbot_conversation_sessions_tenant_id", "chatbot_conversation_sessions", ["tenant_id"])
    op.create_index("ix_chatbot_conversation_sessions_user_id", "chatbot_conversation_sessions", ["user_id"])
    op.create_index("ix_chatbot_conversation_sessions_customer_id", "chatbot_conversation_sessions", ["customer_id"])

    if _is_postgres():
        op.execute("ALTER TABLE chatbot_conversation_sessions ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_chatbot_conversation_sessions
            ON chatbot_conversation_sessions
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_chatbot_conversation_sessions ON chatbot_conversation_sessions")

    op.drop_index("ix_chatbot_conversation_sessions_customer_id", table_name="chatbot_conversation_sessions")
    op.drop_index("ix_chatbot_conversation_sessions_user_id", table_name="chatbot_conversation_sessions")
    op.drop_index("ix_chatbot_conversation_sessions_tenant_id", table_name="chatbot_conversation_sessions")
    op.drop_table("chatbot_conversation_sessions")
