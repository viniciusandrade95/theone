from modules.crm.repo import InMemoryCrmRepo
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.repo.sql import SqlCrmRepo
from modules.crm.service.crm_service import CrmService

from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service.billing_service import BillingService

from modules.analytics.service.analytics_service import AnalyticsService
from modules.messaging.service.inbound_service import InboundMessagingService
from core.config import get_config


class Container:
    def __init__(self):
        self.crm_service: CrmService | None = None
        self.billing_service: BillingService | None = None
        self.analytics_service: AnalyticsService | None = None
        self.inbound_service: InboundMessagingService | None = None


def build_container() -> Container:
    cfg = get_config()
    c = Container()

    # 🔑 Billing (continua in-memory por agora)
    billing_repo = InMemoryBillingRepo()
    billing_service = BillingService(billing_repo)

    # 🔑 CRM — AQUI é o switch
    crm_repo = SqlCrmRepo()          # ← AGORA SQL
    crm_service = CrmService(crm_repo, billing_service)

    # 🔑 Analytics
    analytics_service = AnalyticsService(crm_service)

    # 🔑 Messaging
    inbound_service = InboundMessagingService(crm_service)

    c.billing_service = billing_service
    c.crm_service = crm_service
    c.analytics_service = analytics_service
    c.inbound_service = inbound_service

    return c
