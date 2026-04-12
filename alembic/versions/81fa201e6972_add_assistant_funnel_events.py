"""add assistant funnel events

Revision ID: 81fa201e6972
Revises: 0d4f2c7b1a9e
Create Date: 2026-04-12 17:44:20.143217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '81fa201e6972'
down_revision: Union[str, Sequence[str], None] = '0d4f2c7b1a9e'
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
    """Upgrade schema."""
    meta_type = postgresql.JSONB(astext_type=sa.Text()) if _is_postgres() else sa.JSON()

    op.create_table(
        "assistant_funnel_events",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=True),
        sa.Column("conversation_id", _uuid_type(), nullable=True),
        sa.Column("assistant_session_id", sa.String(length=255), nullable=True),
        sa.Column("customer_id", _uuid_type(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("event_source", sa.String(length=32), nullable=False, server_default="theone"),
        sa.Column("channel", sa.String(length=32), nullable=True),
        sa.Column("related_entity_type", sa.String(length=64), nullable=True),
        sa.Column("related_entity_id", _uuid_type(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("metadata", meta_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "dedupe_key", name="uq_assistant_funnel_events_tenant_dedupe_key"),
    )

    op.create_index("ix_assistant_funnel_events_tenant_id", "assistant_funnel_events", ["tenant_id"])
    op.create_index("ix_assistant_funnel_events_created_at", "assistant_funnel_events", ["created_at"])
    op.create_index("ix_assistant_funnel_events_event_name", "assistant_funnel_events", ["event_name"])
    op.create_index("ix_assistant_funnel_events_trace_id", "assistant_funnel_events", ["trace_id"])
    op.create_index("ix_assistant_funnel_events_conversation_id", "assistant_funnel_events", ["conversation_id"])
    op.create_index("ix_assistant_funnel_events_customer_id", "assistant_funnel_events", ["customer_id"])
    op.create_index("ix_assistant_funnel_events_channel", "assistant_funnel_events", ["channel"])
    op.create_index("ix_assistant_funnel_events_related_entity_id", "assistant_funnel_events", ["related_entity_id"])

    if _is_postgres():
        op.execute("ALTER TABLE assistant_funnel_events ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_assistant_funnel_events
            ON assistant_funnel_events
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    """Downgrade schema."""
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_assistant_funnel_events ON assistant_funnel_events")

    op.drop_index("ix_assistant_funnel_events_related_entity_id", table_name="assistant_funnel_events")
    op.drop_index("ix_assistant_funnel_events_channel", table_name="assistant_funnel_events")
    op.drop_index("ix_assistant_funnel_events_customer_id", table_name="assistant_funnel_events")
    op.drop_index("ix_assistant_funnel_events_conversation_id", table_name="assistant_funnel_events")
    op.drop_index("ix_assistant_funnel_events_trace_id", table_name="assistant_funnel_events")
    op.drop_index("ix_assistant_funnel_events_event_name", table_name="assistant_funnel_events")
    op.drop_index("ix_assistant_funnel_events_created_at", table_name="assistant_funnel_events")
    op.drop_index("ix_assistant_funnel_events_tenant_id", table_name="assistant_funnel_events")
    op.drop_table("assistant_funnel_events")
