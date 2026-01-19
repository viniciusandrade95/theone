from abc import ABC, abstractmethod
from modules.tenants.models.tenant import Tenant


class TenantRepo(ABC):
    @abstractmethod
    def get_by_id(self, tenant_id: str) -> Tenant | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, tenant: Tenant) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, tenant_id: str) -> bool:
        raise NotImplementedError
