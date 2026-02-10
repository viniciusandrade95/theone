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
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        stage: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> list[Customer]: ...

    @abstractmethod
    def add_interaction(self, interaction: Interaction) -> None: ...

    @abstractmethod
    def list_interactions(
        self,
        tenant_id: str,
        customer_id: str,
        *,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> list[Interaction]: ...

    @abstractmethod
    def find_customer_by_phone(self, tenant_id: str, phone: str) -> Customer | None: ...

    @abstractmethod
    def count_customers(self, tenant_id: str, *, query: str | None = None, stage: str | None = None) -> int: ...

    @abstractmethod
    def count_interactions(self, tenant_id: str, customer_id: str, *, query: str | None = None) -> int: ...

    @abstractmethod
    def delete_customer(self, tenant_id: str, customer_id: str) -> None: ...
