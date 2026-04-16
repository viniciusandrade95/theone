"""add billing_subscriptions table (persisted billing)

Revision ID: d60a8820d51e
Revises: 116503276ca7
Create Date: 2026-04-16

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d60a8820d51e"
down_revision: Union[str, Sequence[str], None] = "116503276ca7"
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
    op.create_table(
        "billing_subscriptions",
        sa.Column("tenant_id", _uuid_type(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("tier", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    if _is_postgres():
        op.execute("ALTER TABLE billing_subscriptions ENABLE ROW LEVEL SECURITY")
        # Safe when app.current_tenant_id isn't set: returns NULL -> policy denies.
        op.execute(
            "CREATE POLICY tenant_isolation_billing_subscriptions ON billing_subscriptions USING (tenant_id::text = current_setting('app.current_tenant_id', true))"
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_billing_subscriptions ON billing_subscriptions")

    op.drop_table("billing_subscriptions")

