"""add crm tables

Revision ID: 9f2b1e3c4d5a
Revises: e5903ee13d2d
Create Date: 2026-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f2b1e3c4d5a"
down_revision: Union[str, Sequence[str], None] = "e5903ee13d2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("consent_marketing", sa.Boolean(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_index("ix_customers_phone", "customers", ["phone"])

    op.create_table(
        "interactions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_interactions_tenant_id", "interactions", ["tenant_id"])
    op.create_index("ix_interactions_customer_id", "interactions", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_interactions_customer_id", table_name="interactions")
    op.drop_index("ix_interactions_tenant_id", table_name="interactions")
    op.drop_table("interactions")
    op.drop_index("ix_customers_phone", table_name="customers")
    op.drop_index("ix_customers_tenant_id", table_name="customers")
    op.drop_table("customers")
