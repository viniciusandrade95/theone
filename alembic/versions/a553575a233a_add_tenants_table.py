"""add tenants table

Revision ID: a553575a233a
Revises: aefb199d82c6
Create Date: 2026-01-19 18:20:36.826784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a553575a233a'
down_revision: Union[str, Sequence[str], None] = 'aefb199d82c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
