"""disable RLS on whatsapp_accounts routing table

Revision ID: 116503276ca7
Revises: 3a61a9cdd5e9
Create Date: 2026-04-16

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "116503276ca7"
down_revision: Union[str, Sequence[str], None] = "3a61a9cdd5e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def upgrade() -> None:
    """Upgrade schema."""
    if not _is_postgres():
        return

    # whatsapp_accounts is a routing table used to resolve tenant_id for provider-driven callbacks
    # (inbound/delivery) before any tenancy context exists. RLS here breaks that resolution.
    op.execute("DROP POLICY IF EXISTS tenant_isolation_whatsapp_accounts ON whatsapp_accounts")
    op.execute("ALTER TABLE whatsapp_accounts DISABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    if not _is_postgres():
        return

    op.execute("ALTER TABLE whatsapp_accounts ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation_whatsapp_accounts ON whatsapp_accounts USING (tenant_id::text = current_setting('app.current_tenant_id'))"
    )

