from abc import ABC, abstractmethod
from datetime import datetime
from modules.crm.models import Customer, Interaction


class AnalyticsRepo(ABC):
    @abstractmethod
    def list_customers(self, tenant_id: str) -> list[Customer]: ...

    @abstractmethod
    def list_interactions(self, tenant_id: str) -> list[Interaction]: ...

    @abstractmethod
    def list_customers_created_between(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> list[Customer]: ...
