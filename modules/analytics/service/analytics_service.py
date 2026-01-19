from datetime import datetime
from core.tenancy import require_tenant_id
from modules.analytics.models import AnalyticsSummary
from modules.analytics.repo.analytics_repo import AnalyticsRepo
from modules.crm.models import PipelineStage


class AnalyticsService:
    def __init__(self, repo: AnalyticsRepo):
        self.repo = repo

    def summary(self, *, start: datetime, end: datetime) -> AnalyticsSummary:
        tenant_id = require_tenant_id()

        customers = self.repo.list_customers(tenant_id)
        interactions = self.repo.list_interactions(tenant_id)
        new_customers = self.repo.list_customers_created_between(tenant_id, start, end)

        leads = sum(1 for c in customers if c.stage == PipelineStage.LEAD)
        booked = sum(1 for c in customers if c.stage == PipelineStage.BOOKED)
        completed = sum(1 for c in customers if c.stage == PipelineStage.COMPLETED)

        # retenção básica: clientes com 2+ interações
        interactions_by_customer: dict[str, int] = {}
        for i in interactions:
            interactions_by_customer[i.customer_id] = interactions_by_customer.get(i.customer_id, 0) + 1
        retained = sum(1 for _, count in interactions_by_customer.items() if count >= 2)

        return AnalyticsSummary(
            new_customers=len(new_customers),
            leads=leads,
            booked=booked,
            completed=completed,
            retained_customers=retained,
            total_interactions=len(interactions),
        )
