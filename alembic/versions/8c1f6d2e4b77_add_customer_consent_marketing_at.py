"""add customer consent marketing timestamp

Revision ID: 8c1f6d2e4b77
Revises: c2f2f1e5f9ae
Create Date: 2026-02-09 21:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c1f6d2e4b77"
down_revision: Union[str, Sequence[str], None] = "c2f2f1e5f9ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("consent_marketing_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "consent_marketing_at")
