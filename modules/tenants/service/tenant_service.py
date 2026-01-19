from core.errors import NotFoundError
from modules.tenants.models.tenant import Tenant
from modules.tenants.repo.tenant_repo import TenantRepo


class TenantService:
    def __init__(self, repo: TenantRepo):
        self.repo = repo

    def create_tenant(self, tenant_id: str, name: str) -> Tenant:
        tenant = Tenant.create(tenant_id=tenant_id, name=name)
        self.repo.create(tenant)
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.repo.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant not found", meta={"tenant_id": tenant_id})
        return tenant
