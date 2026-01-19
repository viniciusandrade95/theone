from datetime import datetime
from modules.analytics.repo.analytics_repo import AnalyticsRepo
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.models import Customer, Interaction


class InMemoryAnalyticsRepo(AnalyticsRepo):
    """
    Adapter read-only em cima do InMemoryCrmRepo.
    Em produção isto vira queries agregadas no DB.
    """
    def __init__(self, crm_repo: InMemoryCrmRepo):
        self.crm_repo = crm_repo

    def list_customers(self, tenant_id: str) -> list[Customer]:
        return self.crm_repo.list_customers(tenant_id)

    def list_interactions(self, tenant_id: str) -> list[Interaction]:
        customers = self.crm_repo.list_customers(tenant_id)
        all_interactions: list[Interaction] = []
        for c in customers:
            all_interactions.extend(
                self.crm_repo.list_interactions(tenant_id, c.id)
            )
        return all_interactions

    def list_customers_created_between(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> list[Customer]:
        return [
            c for c in self.crm_repo.list_customers(tenant_id)
            if start <= c.created_at <= end
        ]
