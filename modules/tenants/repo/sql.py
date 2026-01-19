from sqlalchemy.exc import IntegrityError

from core.db.session import db_session
from modules.tenants.repo import TenantRepo
from modules.tenants.models.tenant import Tenant
from modules.tenants.models.tenant_orm import TenantORM


class SqlTenantRepo(TenantRepo):

    def create(self, tenant):
        try:
            with db_session() as session:
                session.add(TenantORM(id=tenant.id, name=tenant.name))
        except IntegrityError:
            raise

    def get(self, tenant_id):
        with db_session() as session:
            row = session.get(TenantORM, tenant_id)
            if not row:
                return None
            return Tenant(id=row.id, name=row.name)
