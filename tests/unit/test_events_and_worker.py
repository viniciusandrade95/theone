import pytest
from core.events import EventBus, MessageReceived
from core.tenancy import set_tenant_id, clear_tenant_id
from core.errors import ForbiddenError

from modules.crm.repo import InMemoryCrmRepo
from modules.crm.service import CrmService

from modules.messaging.service import InboundMessagingService
from modules.messaging.api.inbound_entrypoint import accept_inbound_webhook

from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService
from modules.billing.models import PlanTier

from tasks.workers.messaging.inbound_worker import InboundMessageWorker


@pytest.fixture(autouse=True)
def tenancy_context():
    clear_tenant_id()
    yield
    clear_tenant_id()


def _setup_bus_with_worker(crm: CrmService, billing: BillingService) -> EventBus:
    inbound_service = InboundMessagingService(crm)
    worker = InboundMessageWorker(inbound_service, billing)
    bus = EventBus()
    bus.subscribe(MessageReceived, worker.handle)
    return bus


def test_starter_blocks_whatsapp_in_worker():
    crm_repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    crm = CrmService(crm_repo, billing)

    set_tenant_id("t1")
    billing.set_plan(tier=PlanTier.STARTER)
    customer = crm.create_customer(name="Bea", phone="351111")

    bus = _setup_bus_with_worker(crm, billing)

    with pytest.raises(ForbiddenError):
        accept_inbound_webhook(
            {"message_id": "m1", "from_phone": "351111", "text": "Oi"},
            bus
        )

    # confirma que nada foi escrito
    set_tenant_id("t1")
    interactions = crm.list_interactions(customer_id=customer.id)
    assert len(interactions) == 0


def test_pro_allows_whatsapp_in_worker():
    crm_repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    crm = CrmService(crm_repo, billing)

    set_tenant_id("t1")
    billing.set_plan(tier=PlanTier.PRO)
    customer = crm.create_customer(name="Bea", phone="351111")

    bus = _setup_bus_with_worker(crm, billing)

    res = accept_inbound_webhook(
        {"message_id": "m1", "from_phone": "351111", "text": "Oi"},
        bus
    )
    assert res["status"] == "accepted"

    set_tenant_id("t1")
    interactions = crm.list_interactions(customer_id=customer.id)
    assert len(interactions) == 1
    assert interactions[0].type == "whatsapp"
    assert interactions[0].content == "Oi"
