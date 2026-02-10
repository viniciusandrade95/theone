from sqlalchemy.exc import IntegrityError
from uuid import UUID

from core.db.session import db_session
from modules.tenants.repo import TenantRepo
from modules.tenants.models.tenant import Tenant
from modules.tenants.models.tenant_orm import TenantORM


class SqlTenantRepo(TenantRepo):
    def _coerce_uuid(self, value: str):
        try:
            return UUID(value)
        except (TypeError, ValueError):
            return value

    def create(self, tenant):
        try:
            with db_session() as session:
                session.add(TenantORM(id=self._coerce_uuid(tenant.id), name=tenant.name))
        except IntegrityError:
            raise

    def get(self, tenant_id):
        with db_session() as session:
            row = session.get(TenantORM, self._coerce_uuid(tenant_id))
            if not row:
                return None
            return Tenant(id=str(row.id), name=row.name)
