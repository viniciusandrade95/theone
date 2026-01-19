from modules.tenants.repo.tenant_repo import TenantRepo
from modules.tenants.models.tenant import Tenant
from core.errors import ConflictError


class InMemoryTenantRepo(TenantRepo):

    def __init__(self):
        self._items: dict[str, Tenant] = {}

    def create(self, tenant: Tenant) -> None:
        if tenant.id in self._items:
            raise ConflictError("tenant already exists")
        self._items[tenant.id] = tenant

    def get(self, tenant_id: str) -> Tenant | None:
        return self._items.get(tenant_id)
