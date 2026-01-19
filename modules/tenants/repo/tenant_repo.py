from abc import ABC, abstractmethod
from modules.tenants.models.tenant import Tenant


class TenantRepo(ABC):

    @abstractmethod
    def create(self, *, id: str, name: str) -> Tenant:
        pass

    @abstractmethod
    def get(self, tenant_id: str) -> Tenant | None:
        pass
