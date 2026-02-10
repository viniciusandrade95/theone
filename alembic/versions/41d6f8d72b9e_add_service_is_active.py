"""add service is_active flag

Revision ID: 41d6f8d72b9e
Revises: 8c1f6d2e4b77
Create Date: 2026-02-09 22:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "41d6f8d72b9e"
down_revision: Union[str, Sequence[str], None] = "8c1f6d2e4b77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("services", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_services_tenant_active", "services", ["tenant_id", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_services_tenant_active", table_name="services")
    op.drop_column("services", "is_active")
