from modules.tenants.repo.tenant_repo import TenantRepo
from modules.tenants.models.tenant import Tenant


class InMemoryTenantRepo(TenantRepo):

    def __init__(self):
        self._tenants: dict[str, Tenant] = {}

    def create(self, *, id: str, name: str) -> Tenant:
        tenant = Tenant(id=id, name=name)
        self._tenants[id] = tenant
        return tenant

    def get(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)
