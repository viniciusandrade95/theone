from dataclasses import dataclass

from core.events import EventBus, MessageReceived
from modules.tenants.repo.in_memory import InMemoryTenantRepo
from modules.tenants.service.tenant_service import TenantService

from modules.iam.repo.in_memory import InMemoryUserRepo
from modules.billing.repo.in_memory import InMemoryBillingRepo
from modules.billing.service.billing_service import BillingService

from modules.crm.repo.in_memory import InMemoryCrmRepo
from modules.crm.service.crm_service import CrmService

from modules.messaging.service.inbound_service import InboundMessagingService
from tasks.workers.messaging.inbound_worker import InboundMessageWorker

from modules.analytics.repo.in_memory import InMemoryAnalyticsRepo
from modules.analytics.service.analytics_service import AnalyticsService


@dataclass
class Container:
    # infra
    bus: EventBus

    # repos
    tenants_repo: InMemoryTenantRepo
    users_repo: InMemoryUserRepo
    billing_repo: InMemoryBillingRepo
    crm_repo: InMemoryCrmRepo

    # services
    tenants: TenantService
    billing: BillingService
    crm: CrmService
    inbound: InboundMessagingService
    analytics: AnalyticsService

    # worker
    inbound_worker: InboundMessageWorker


def build_container() -> Container:
    bus = EventBus()

    tenants_repo = InMemoryTenantRepo()
    users_repo = InMemoryUserRepo()
    billing_repo = InMemoryBillingRepo()
    crm_repo = InMemoryCrmRepo()

    billing = BillingService(
        billing_repo,
        count_users=users_repo.count_users,
        count_customers=crm_repo.count_customers,
    )

    tenants = TenantService(tenants_repo)

    crm = CrmService(crm_repo, billing)

    inbound = InboundMessagingService(crm)
    inbound_worker = InboundMessageWorker(inbound, billing)

    # event wiring
    bus.subscribe(MessageReceived, inbound_worker.handle)

    analytics_repo = InMemoryAnalyticsRepo(crm_repo)
    analytics = AnalyticsService(analytics_repo)

    return Container(
        bus=bus,
        tenants_repo=tenants_repo,
        users_repo=users_repo,
        billing_repo=billing_repo,
        crm_repo=crm_repo,
        tenants=tenants,
        billing=billing,
        crm=crm,
        inbound=inbound,
        analytics=analytics,
        inbound_worker=inbound_worker,
    )
