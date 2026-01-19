from sqlalchemy import select
from core.db.session import db_session
from modules.tenants.models.tenant import Tenant
from modules.tenants.models.tenant_orm import TenantORM


class TenantsRepo:

    def create(self, *, id: str, name: str) -> Tenant:
        with db_session() as session:
            orm = TenantORM(id=id, name=name)
            session.add(orm)

            return Tenant(id=orm.id, name=orm.name)

    def get(self, tenant_id: str) -> Tenant | None:
        with db_session() as session:
            stmt = select(TenantORM).where(TenantORM.id == tenant_id)
            orm = session.execute(stmt).scalar_one_or_none()

            if not orm:
                return None

            return Tenant(id=orm.id, name=orm.name)
