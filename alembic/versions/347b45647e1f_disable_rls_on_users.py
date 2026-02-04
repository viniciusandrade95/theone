"""disable_rls_on_users

Revision ID: 347b45647e1f
Revises: 7b4a2d0b2b9d
Create Date: 2026-02-03 19:14:43.583560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '347b45647e1f'
down_revision: Union[str, Sequence[str], None] = '7b4a2d0b2b9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"

def upgrade():
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
        op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")

def downgrade():
    if _is_postgres():
        op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY tenant_isolation_users ON users "
            "USING (tenant_id::text = current_setting('app.current_tenant_id'))"
        )
