"""add outbound templates and messages

Revision ID: b0c2d8e8f9a0
Revises: a8c3f1d2b7c1
Create Date: 2026-04-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b0c2d8e8f9a0"
down_revision: Union[str, Sequence[str], None] = "a8c3f1d2b7c1"
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
        "message_templates",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="whatsapp"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_message_templates_tenant_type", "message_templates", ["tenant_id", "type"])
    op.create_index("ix_message_templates_tenant_active", "message_templates", ["tenant_id", "is_active"])

    op.create_table(
        "outbound_messages",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", _uuid_type(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("appointment_id", _uuid_type(), sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("template_id", _uuid_type(), sa.ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("rendered_body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_by_user_id", _uuid_type(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_outbound_messages_tenant_status", "outbound_messages", ["tenant_id", "status"])
    op.create_index("ix_outbound_messages_tenant_customer", "outbound_messages", ["tenant_id", "customer_id"])
    op.create_index("ix_outbound_messages_tenant_template", "outbound_messages", ["tenant_id", "template_id"])
    op.create_index("ix_outbound_messages_tenant_created_at", "outbound_messages", ["tenant_id", "created_at"])

    if _is_postgres():
        op.execute("ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_message_templates
            ON message_templates
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )

        op.execute("ALTER TABLE outbound_messages ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_outbound_messages
            ON outbound_messages
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_outbound_messages ON outbound_messages")
        op.execute("DROP POLICY IF EXISTS tenant_isolation_message_templates ON message_templates")

    op.drop_index("ix_outbound_messages_tenant_created_at", table_name="outbound_messages")
    op.drop_index("ix_outbound_messages_tenant_template", table_name="outbound_messages")
    op.drop_index("ix_outbound_messages_tenant_customer", table_name="outbound_messages")
    op.drop_index("ix_outbound_messages_tenant_status", table_name="outbound_messages")
    op.drop_table("outbound_messages")

    op.drop_index("ix_message_templates_tenant_active", table_name="message_templates")
    op.drop_index("ix_message_templates_tenant_type", table_name="message_templates")
    op.drop_table("message_templates")

