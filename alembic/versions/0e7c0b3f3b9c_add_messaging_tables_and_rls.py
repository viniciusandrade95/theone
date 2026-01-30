"""add messaging tables and rls

Revision ID: 0e7c0b3f3b9c
Revises: bef04fb0b750
Create Date: 2026-02-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0e7c0b3f3b9c"
down_revision: Union[str, Sequence[str], None] = "bef04fb0b750"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade():
    op.create_table(
        "whatsapp_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("phone_number_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider", "phone_number_id", name="uq_whatsapp_accounts_provider_phone"),
    )
    op.create_index("ix_whatsapp_accounts_tenant_id", "whatsapp_accounts", ["tenant_id"])

    op.create_table(
        "webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("external_event_id", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("signature_valid", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="received"),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id",
            "provider",
            "external_event_id",
            name="uq_webhook_events_tenant_provider_external",
        ),
    )
    op.create_index("ix_webhook_events_tenant_id", "webhook_events", ["tenant_id"])

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False, server_default="open"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "customer_id",
            "channel",
            name="uq_conversations_tenant_customer_channel",
        ),
    )
    op.create_index("ix_conversations_tenant_id", "conversations", ["tenant_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_message_id", sa.String(), nullable=False),
        sa.Column("from_phone", sa.String(), nullable=False),
        sa.Column("to_phone", sa.String(), nullable=True),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="received"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "provider_message_id", name="uq_messages_tenant_provider_message"),
    )
    op.create_index("ix_messages_tenant_id", "messages", ["tenant_id"])

    if _is_postgres():
        op.execute("ALTER TABLE customers ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE interactions ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE whatsapp_accounts ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE conversations ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE messages ENABLE ROW LEVEL SECURITY")

        op.execute(
            "CREATE POLICY tenant_isolation_customers ON customers USING (tenant_id::text = current_setting('app.current_tenant_id'))"
        )
        op.execute(
            "CREATE POLICY tenant_isolation_interactions ON interactions USING (tenant_id::text = current_setting('app.current_tenant_id'))"
        )
        op.execute(
            "CREATE POLICY tenant_isolation_whatsapp_accounts ON whatsapp_accounts USING (tenant_id::text = current_setting('app.current_tenant_id'))"
        )
        op.execute(
            "CREATE POLICY tenant_isolation_webhook_events ON webhook_events USING (tenant_id::text = current_setting('app.current_tenant_id'))"
        )
        op.execute(
            "CREATE POLICY tenant_isolation_conversations ON conversations USING (tenant_id::text = current_setting('app.current_tenant_id'))"
        )
        op.execute(
            "CREATE POLICY tenant_isolation_messages ON messages USING (tenant_id::text = current_setting('app.current_tenant_id'))"
        )


def downgrade():
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_messages ON messages")
        op.execute("DROP POLICY IF EXISTS tenant_isolation_conversations ON conversations")
        op.execute("DROP POLICY IF EXISTS tenant_isolation_webhook_events ON webhook_events")
        op.execute("DROP POLICY IF EXISTS tenant_isolation_whatsapp_accounts ON whatsapp_accounts")
        op.execute("DROP POLICY IF EXISTS tenant_isolation_interactions ON interactions")
        op.execute("DROP POLICY IF EXISTS tenant_isolation_customers ON customers")

    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("webhook_events")
    op.drop_table("whatsapp_accounts")
