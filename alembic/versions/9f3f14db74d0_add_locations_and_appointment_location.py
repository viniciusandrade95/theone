"""add locations and appointment location

Revision ID: 9f3f14db74d0
Revises: f7c342e16bec
Create Date: 2026-02-09 19:05:00.000000

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9f3f14db74d0"
down_revision: Union[str, Sequence[str], None] = "f7c342e16bec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind is not None and bind.dialect.name == "postgresql"


def _uuid_type():
    if _is_postgres():
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _json_type():
    if _is_postgres():
        return postgresql.JSONB()
    return sa.JSON()


def _insert_default_locations_and_backfill_appointments() -> None:
    bind = op.get_bind()
    tenant_rows = bind.execute(sa.text("SELECT id FROM tenants")).fetchall()

    for row in tenant_rows:
        tenant_id = str(row[0])
        default_location_id = str(uuid.uuid4())
        bind.execute(
            sa.text(
                """
                INSERT INTO locations (
                    id,
                    tenant_id,
                    name,
                    timezone,
                    is_active,
                    allow_overlaps,
                    created_at,
                    updated_at
                ) VALUES (
                    :id,
                    :tenant_id,
                    :name,
                    :timezone,
                    :is_active,
                    :allow_overlaps,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": default_location_id,
                "tenant_id": tenant_id,
                "name": "Main Location",
                "timezone": "UTC",
                "is_active": True,
                "allow_overlaps": False,
            },
        )

        bind.execute(
            sa.text(
                """
                UPDATE appointments
                SET location_id = :location_id
                WHERE tenant_id = :tenant_id
                  AND location_id IS NULL
                """
            ),
            {"location_id": default_location_id, "tenant_id": tenant_id},
        )


def upgrade():
    op.create_table(
        "locations",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column(
            "tenant_id",
            _uuid_type(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("address_line1", sa.Text(), nullable=True),
        sa.Column("address_line2", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("postcode", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hours_json", _json_type(), nullable=True),
        sa.Column("allow_overlaps", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_locations_tenant_active", "locations", ["tenant_id", "is_active"])
    op.create_index("ix_locations_tenant_name", "locations", ["tenant_id", "name"])
    op.create_index("ix_locations_tenant_deleted", "locations", ["tenant_id", "deleted_at"])

    op.add_column("appointments", sa.Column("location_id", _uuid_type(), nullable=True))
    op.create_foreign_key(
        "fk_appointments_location_id_locations",
        source_table="appointments",
        referent_table="locations",
        local_cols=["location_id"],
        remote_cols=["id"],
        ondelete="RESTRICT",
    )

    _insert_default_locations_and_backfill_appointments()

    op.alter_column("appointments", "location_id", nullable=False)
    op.create_index(
        "ix_appointments_tenant_location_starts",
        "appointments",
        ["tenant_id", "location_id", "starts_at"],
    )

    if _is_postgres():
        op.execute("ALTER TABLE locations ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_locations
            ON locations
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade():
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_locations ON locations")

    op.drop_index("ix_appointments_tenant_location_starts", table_name="appointments")
    op.drop_constraint("fk_appointments_location_id_locations", "appointments", type_="foreignkey")
    op.drop_column("appointments", "location_id")

    op.drop_index("ix_locations_tenant_deleted", table_name="locations")
    op.drop_index("ix_locations_tenant_name", table_name="locations")
    op.drop_index("ix_locations_tenant_active", table_name="locations")
    op.drop_table("locations")
