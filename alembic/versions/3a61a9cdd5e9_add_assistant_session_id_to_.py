"""add assistant session id to conversations

Revision ID: 3a61a9cdd5e9
Revises: 81fa201e6972
Create Date: 2026-04-12 19:21:27.480427

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a61a9cdd5e9'
down_revision: Union[str, Sequence[str], None] = '81fa201e6972'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("conversations", sa.Column("assistant_session_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("conversations", "assistant_session_id")
