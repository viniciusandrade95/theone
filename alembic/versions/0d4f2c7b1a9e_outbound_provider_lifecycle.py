"""outbound provider lifecycle

Revision ID: 0d4f2c7b1a9e
Revises: 7c1e2a9b4d3f
Create Date: 2026-04-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0d4f2c7b1a9e"
down_revision: Union[str, Sequence[str], None] = "7c1e2a9b4d3f"
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
    # Expand outbound_messages with provider-backed lifecycle fields.
    op.add_column("outbound_messages", sa.Column("provider", sa.String(length=32), nullable=True))
    op.add_column("outbound_messages", sa.Column("provider_message_id", sa.String(length=255), nullable=True))
    op.add_column("outbound_messages", sa.Column("recipient", sa.String(length=255), nullable=True))
    op.add_column("outbound_messages", sa.Column("delivery_status", sa.String(length=32), nullable=True))
    op.add_column("outbound_messages", sa.Column("delivery_status_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbound_messages", sa.Column("error_code", sa.String(length=64), nullable=True))
    op.add_column("outbound_messages", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    op.add_column("outbound_messages", sa.Column("trigger_type", sa.String(length=32), nullable=True))
    op.add_column("outbound_messages", sa.Column("trace_id", sa.String(length=128), nullable=True))
    op.add_column("outbound_messages", sa.Column("conversation_id", _uuid_type(), nullable=True))
    op.add_column("outbound_messages", sa.Column("assistant_session_id", sa.String(length=255), nullable=True))
    op.add_column("outbound_messages", sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbound_messages", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbound_messages", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_outbound_messages_provider", "outbound_messages", ["provider"])
    op.create_index("ix_outbound_messages_provider_message_id", "outbound_messages", ["provider_message_id"])
    op.create_index("ix_outbound_messages_delivery_status", "outbound_messages", ["delivery_status"])
    op.create_unique_constraint(
        "uq_outbound_messages_tenant_idempotency_key",
        "outbound_messages",
        ["tenant_id", "idempotency_key"],
    )

    op.create_table(
        "outbound_delivery_events",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_event_id", sa.String(length=255), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", _json_type(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "provider", "external_event_id", name="uq_outbound_delivery_tenant_provider_event"),
    )
    op.create_index("ix_outbound_delivery_events_tenant_id", "outbound_delivery_events", ["tenant_id"])
    op.create_index("ix_outbound_delivery_events_provider_message_id", "outbound_delivery_events", ["provider_message_id"])

    if _is_postgres():
        op.execute("ALTER TABLE outbound_delivery_events ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_outbound_delivery_events
            ON outbound_delivery_events
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_outbound_delivery_events ON outbound_delivery_events")

    op.drop_index("ix_outbound_delivery_events_provider_message_id", table_name="outbound_delivery_events")
    op.drop_index("ix_outbound_delivery_events_tenant_id", table_name="outbound_delivery_events")
    op.drop_table("outbound_delivery_events")

    op.drop_constraint("uq_outbound_messages_tenant_idempotency_key", "outbound_messages", type_="unique")
    op.drop_index("ix_outbound_messages_delivery_status", table_name="outbound_messages")
    op.drop_index("ix_outbound_messages_provider_message_id", table_name="outbound_messages")
    op.drop_index("ix_outbound_messages_provider", table_name="outbound_messages")

    op.drop_column("outbound_messages", "failed_at")
    op.drop_column("outbound_messages", "delivered_at")
    op.drop_column("outbound_messages", "scheduled_for")
    op.drop_column("outbound_messages", "assistant_session_id")
    op.drop_column("outbound_messages", "conversation_id")
    op.drop_column("outbound_messages", "trace_id")
    op.drop_column("outbound_messages", "trigger_type")
    op.drop_column("outbound_messages", "idempotency_key")
    op.drop_column("outbound_messages", "error_code")
    op.drop_column("outbound_messages", "delivery_status_updated_at")
    op.drop_column("outbound_messages", "delivery_status")
    op.drop_column("outbound_messages", "recipient")
    op.drop_column("outbound_messages", "provider_message_id")
    op.drop_column("outbound_messages", "provider")

