"""add tenants table

Revision ID: e5903ee13d2d
Revises: a553575a233a
Create Date: 2026-01-19 18:23:13.177035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5903ee13d2d'
down_revision: Union[str, Sequence[str], None] = 'a553575a233a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
