from sqlalchemy.exc import IntegrityError
from core.db.session import get_session
from modules.tenants.repo import TenantRepo
from modules.tenants.models.tenant import TenantORM

class SqlTenantRepo(TenantRepo):

    def create(self, tenant):
        db = get_session()
        try:
            db.add(TenantORM(id=tenant.id, name=tenant.name))
            db.commit()
        except IntegrityError:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, tenant_id):
        db = get_session()
        try:
            row = db.get(TenantORM, tenant_id)
            if not row:
                return None
            return tenant.__class__(id=row.id, name=row.name)
        finally:
            db.close()
