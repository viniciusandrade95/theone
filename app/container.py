from modules.crm.repo import InMemoryCrmRepo
from modules.crm.repo.sql import SqlCrmRepo
from modules.crm.service.crm_service import CrmService
from modules.tenants.repo.in_memory import InMemoryTenantRepo
from modules.tenants.service.tenant_service import TenantService


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

    # 🔑 Tenants (IN-MEMORY por agora)
    tenant_repo = InMemoryTenantRepo()
    tenant_service = TenantService(tenant_repo)

    # 🔑 Billing
    billing_repo = InMemoryBillingRepo()
    billing_service = BillingService(billing_repo)

    # 🔑 CRM
    crm_repo = SqlCrmRepo()
    crm_service = CrmService(crm_repo, billing_service)

    # 🔑 Analytics
    analytics_service = AnalyticsService(crm_service)

    # 🔑 Messaging
    inbound_service = InboundMessagingService(crm_service)

    # wire
    c.tenant_service = tenant_service
    c.billing_service = billing_service
    c.crm_service = crm_service
    c.analytics_service = analytics_service
    c.inbound_service = inbound_service

    return c

