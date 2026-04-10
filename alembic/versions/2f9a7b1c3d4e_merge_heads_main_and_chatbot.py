"""merge heads: main and chatbot

Revision ID: 2f9a7b1c3d4e
Revises: b0c2d8e8f9a0, 1d2c3e4f5a6b
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union


revision: str = "2f9a7b1c3d4e"
down_revision: Union[str, Sequence[str], None] = ("b0c2d8e8f9a0", "1d2c3e4f5a6b")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge migration (no-op).
    pass


def downgrade() -> None:
    # Merge migration (no-op).
    pass

