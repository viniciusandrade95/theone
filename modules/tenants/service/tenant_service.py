from core.errors import ConflictError, NotFoundError
from modules.tenants.models.tenant import Tenant
from modules.tenants.repo.tenant_repo import TenantRepo


class TenantService:
    def __init__(self, repo: TenantRepo):
        self.repo = repo

    def create_tenant(self, tenant_id: str, name: str) -> Tenant:
        if self.repo.get(tenant_id):
            raise ConflictError("tenant_already_exists", meta={"tenant_id": tenant_id})
        tenant = Tenant.create(tenant_id=tenant_id, name=name)
        self.repo.create(tenant)
        return tenant

    def get_or_fail(self, tenant_id: str) -> Tenant:
        tenant = self.repo.get(tenant_id)
        if tenant is None:
            raise NotFoundError("tenant_not_found", meta={"tenant_id": tenant_id})
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        return self.get_or_fail(tenant_id)

    def exists(self, tenant_id: str) -> bool:
        return self.repo.get(tenant_id) is not None
