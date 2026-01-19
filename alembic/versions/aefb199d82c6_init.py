"""init

Revision ID: aefb199d82c6
Revises: 4c121759e629
Create Date: 2026-01-19 15:55:10.012951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aefb199d82c6'
down_revision: Union[str, Sequence[str], None] = '4c121759e629'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
