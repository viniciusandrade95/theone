"""add audit log and soft delete columns

Revision ID: e1f8c4ab92de
Revises: d4b51a5a6bce
Create Date: 2026-02-10 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e1f8c4ab92de"
down_revision: Union[str, Sequence[str], None] = "d4b51a5a6bce"
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


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
        sa.Column(
            "tenant_id",
            _uuid_type(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", _uuid_type(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", _uuid_type(), nullable=False),
        sa.Column("before", _json_type(), nullable=True),
        sa.Column("after", _json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_tenant_created_at", "audit_log", ["tenant_id", "created_at"])
    op.create_index("ix_audit_log_tenant_entity", "audit_log", ["tenant_id", "entity_type", "entity_id"])

    op.add_column("customers", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("services", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_customers_tenant_deleted", "customers", ["tenant_id", "deleted_at"])
    op.create_index("ix_services_tenant_deleted", "services", ["tenant_id", "deleted_at"])
    op.create_index("ix_appointments_tenant_deleted", "appointments", ["tenant_id", "deleted_at"])

    if _is_postgres():
        op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY")
        op.execute(
            """
            CREATE POLICY tenant_isolation_audit_log
            ON audit_log
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    if _is_postgres():
        op.execute("DROP POLICY IF EXISTS tenant_isolation_audit_log ON audit_log")

    op.drop_index("ix_appointments_tenant_deleted", table_name="appointments")
    op.drop_index("ix_services_tenant_deleted", table_name="services")
    op.drop_index("ix_customers_tenant_deleted", table_name="customers")

    op.drop_column("appointments", "deleted_at")
    op.drop_column("services", "deleted_at")
    op.drop_column("customers", "deleted_at")

    op.drop_index("ix_audit_log_tenant_entity", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_created_at", table_name="audit_log")
    op.drop_table("audit_log")
