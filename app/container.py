from modules.analytics.repo.sql import SqlAnalyticsRepo
from modules.analytics.service.analytics_service import AnalyticsService
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service.billing_service import BillingService
from modules.crm.repo.in_memory import InMemoryCrmRepo
from modules.crm.repo.sql import SqlCrmRepo
from modules.crm.service.crm_service import CrmService
from modules.iam.repo.in_memory import InMemoryUserRepo
from modules.messaging.repo.sql import SqlMessagingRepo
from modules.messaging.service.inbound_service import InboundMessagingService
from modules.messaging.service.inbound_webhook_service import InboundWebhookService
from modules.tenants.repo.sql import SqlTenantRepo
from modules.tenants.service.tenant_service import TenantService


class Container:
    def __init__(self):
        self.crm_service: CrmService | None = None
        self.billing_service: BillingService | None = None
        self.analytics_service: AnalyticsService | None = None
        self.inbound_service: InboundMessagingService | None = None
        self.users_repo: InMemoryUserRepo | None = None
        self.crm: CrmService | None = None
        self.billing: BillingService | None = None
        self.analytics: AnalyticsService | None = None
        self.tenant_service: TenantService | None = None
        self.messaging_repo: SqlMessagingRepo | None = None
        self.inbound_webhook_service: InboundWebhookService | None = None


def build_container() -> Container:
    c = Container()

    # 🔑 Tenants (IN-MEMORY por agora)
    tenant_repo = SqlTenantRepo()
    tenant_service = TenantService(tenant_repo)

    # 🔑 Billing
    billing_repo = InMemoryBillingRepo()
    billing_service = BillingService(billing_repo)

    # 🔑 CRM
    crm_repo = SqlCrmRepo()          #SqlCrmRepo()
    crm_service = CrmService(crm_repo, billing_service)

    # 🔑 Analytics
    analytics_repo = SqlAnalyticsRepo()
    analytics_service = AnalyticsService(analytics_repo)

    # 🔑 Messaging
    messaging_repo = SqlMessagingRepo()
    inbound_service = InboundMessagingService(crm_service)
    inbound_webhook_service = InboundWebhookService(messaging_repo, crm_service, billing_service)

    # 🔑 IAM
    users_repo = InMemoryUserRepo()

    # wire
    c.tenant_service = tenant_service
    c.billing_service = billing_service
    c.crm_service = crm_service
    c.analytics_service = analytics_service
    c.inbound_service = inbound_service
    c.messaging_repo = messaging_repo
    c.users_repo = users_repo
    c.crm = crm_service
    c.billing = billing_service
    c.analytics = analytics_service
    c.inbound_webhook_service = inbound_webhook_service

    return c
