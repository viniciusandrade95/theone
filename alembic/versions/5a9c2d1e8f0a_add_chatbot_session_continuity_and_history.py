"""add chatbot session continuity and history

Revision ID: 5a9c2d1e8f0a
Revises: 3a1b2c3d4e5f
Create Date: 2026-04-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5a9c2d1e8f0a"
down_revision: Union[str, Sequence[str], None] = "3a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def _uuid_type():
    if _is_postgres():
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _json_type():
    if _is_postgres():
        return postgresql.JSONB()
    return sa.JSON()


def upgrade() -> None:
    # Extend chatbot sessions with compact assistant continuity state.
    op.add_column("chatbot_conversation_sessions", sa.Column("last_intent", sa.String(length=80), nullable=True))
    op.add_column("chatbot_conversation_sessions", sa.Column("last_intent_confidence", sa.Float(), nullable=True))
    op.add_column("chatbot_conversation_sessions", sa.Column("state_payload", _json_type(), nullable=True))
    op.add_column("chatbot_conversation_sessions", sa.Column("context_payload", _json_type(), nullable=True))
    op.add_column(
        "chatbot_conversation_sessions",
        sa.Column("conversation_epoch", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "chatbot_conversation_messages",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column(
            "conversation_id",
            _uuid_type(),
            sa.ForeignKey("chatbot_conversation_sessions.conversation_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", _uuid_type(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("surface", sa.String(length=64), nullable=False, server_default="dashboard"),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=80), nullable=True),
        sa.Column("epoch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meta", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_chatbot_conversation_messages_conversation_id",
        "chatbot_conversation_messages",
        ["conversation_id"],
    )
    op.create_index("ix_chatbot_conversation_messages_tenant_id", "chatbot_conversation_messages", ["tenant_id"])
    op.create_index("ix_chatbot_conversation_messages_user_id", "chatbot_conversation_messages", ["user_id"])

    if _is_postgres():
        op.execute("ALTER TABLE chatbot_conversation_messages ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_chatbot_conversation_messages
            ON chatbot_conversation_messages
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_chatbot_conversation_messages ON chatbot_conversation_messages")

    op.drop_index("ix_chatbot_conversation_messages_user_id", table_name="chatbot_conversation_messages")
    op.drop_index("ix_chatbot_conversation_messages_tenant_id", table_name="chatbot_conversation_messages")
    op.drop_index("ix_chatbot_conversation_messages_conversation_id", table_name="chatbot_conversation_messages")
    op.drop_table("chatbot_conversation_messages")

    op.drop_column("chatbot_conversation_sessions", "conversation_epoch")
    op.drop_column("chatbot_conversation_sessions", "context_payload")
    op.drop_column("chatbot_conversation_sessions", "state_payload")
    op.drop_column("chatbot_conversation_sessions", "last_intent_confidence")
    op.drop_column("chatbot_conversation_sessions", "last_intent")

