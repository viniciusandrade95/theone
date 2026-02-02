from abc import ABC, abstractmethod
from modules.crm.models import Customer, Interaction


class CrmRepo(ABC):
    @abstractmethod
    def create_customer(self, customer: Customer) -> None: ...

    @abstractmethod
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...

    @abstractmethod
    def update_customer(self, customer: Customer) -> None: ...

    @abstractmethod
    def list_customers(
        self,
        tenant_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
    ) -> list[Customer]: ...

    @abstractmethod
    def add_interaction(self, interaction: Interaction) -> None: ...

    @abstractmethod
    def list_interactions(self, tenant_id: str, customer_id: str) -> list[Interaction]: ...

    @abstractmethod
    def find_customer_by_phone(self, tenant_id: str, phone: str) -> Customer | None: ...

    @abstractmethod
    def count_customers(self, tenant_id: str, *, search: str | None = None) -> int: ...

    @abstractmethod
    def delete_customer(self, tenant_id: str, customer_id: str) -> None: ...
