"""add tenant settings table

Revision ID: d4b51a5a6bce
Revises: 41d6f8d72b9e
Create Date: 2026-02-09 22:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d4b51a5a6bce"
down_revision: Union[str, Sequence[str], None] = "41d6f8d72b9e"
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
    op.create_table(
        "tenant_settings",
        sa.Column(
            "tenant_id",
            _uuid_type(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("business_name", sa.Text(), nullable=True),
        sa.Column("default_timezone", sa.Text(), nullable=False, server_default="UTC"),
        sa.Column("currency", sa.String(length=12), nullable=False, server_default="USD"),
        sa.Column("calendar_default_view", sa.String(length=16), nullable=False, server_default="week"),
        sa.Column(
            "default_location_id",
            _uuid_type(),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("primary_color", sa.String(length=32), nullable=True),
        sa.Column("logo_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    if _is_postgres():
        op.execute("ALTER TABLE tenant_settings ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_tenant_settings
            ON tenant_settings
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_tenant_settings ON tenant_settings")
    op.drop_table("tenant_settings")
