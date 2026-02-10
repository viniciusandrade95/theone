"""add appointment lifecycle fields

Revision ID: c2f2f1e5f9ae
Revises: 9f3f14db74d0
Create Date: 2026-02-09 20:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c2f2f1e5f9ae"
down_revision: Union[str, Sequence[str], None] = "9f3f14db74d0"
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
    op.add_column("appointments", sa.Column("cancelled_reason", sa.Text(), nullable=True))
    op.add_column(
        "appointments",
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("appointments", sa.Column("created_by_user_id", _uuid_type(), nullable=True))
    op.add_column("appointments", sa.Column("updated_by_user_id", _uuid_type(), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "updated_by_user_id")
    op.drop_column("appointments", "created_by_user_id")
    op.drop_column("appointments", "status_updated_at")
    op.drop_column("appointments", "cancelled_reason")
