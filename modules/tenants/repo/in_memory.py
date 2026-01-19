from core.errors import ConflictError
from modules.tenants.models.tenant import Tenant
from modules.tenants.repo.tenant_repo import TenantRepo


class InMemoryTenantRepo(TenantRepo):
    def __init__(self):
        self._tenants: dict[str, Tenant] = {}

    def get_by_id(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def exists(self, tenant_id: str) -> bool:
        return tenant_id in self._tenants

    def create(self, tenant: Tenant) -> None:
        if self.exists(tenant.id):
            raise ConflictError("Tenant already exists", meta={"tenant_id": tenant.id})
        self._tenants[tenant.id] = tenant
