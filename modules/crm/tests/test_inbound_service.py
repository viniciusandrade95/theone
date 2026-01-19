import pytest
from core.errors import NotFoundError, ValidationError
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.service import CrmService
from modules.messaging.service import InboundMessagingService
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService


@pytest.fixture(autouse=True)
def tenancy_context():
    clear_tenant_id()
    yield
    clear_tenant_id()


def test_inbound_creates_interaction_on_customer():
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    crm = CrmService(repo, billing)
    svc = InboundMessagingService(crm)

    set_tenant_id("t1")
    customer = crm.create_customer(name="Sofia", phone="351999")

    res = svc.handle_inbound({"message_id": "m1", "from_phone": "351999", "text": "Olá!"})
    assert res["status"] == "ok"
    assert res["customer_id"] == customer.id

    interactions = crm.list_interactions(customer_id=customer.id)
    assert len(interactions) == 1
    assert interactions[0].type == "whatsapp"
    assert interactions[0].content == "Olá!"


def test_inbound_fails_if_customer_not_found():
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    crm = CrmService(repo, billing)
    svc = InboundMessagingService(crm)

    set_tenant_id("t1")
    with pytest.raises(NotFoundError):
        svc.handle_inbound({"message_id": "m1", "from_phone": "nope", "text": "Oi"})


def test_inbound_validates_payload():
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    crm = CrmService(repo, billing)
    svc = InboundMessagingService(crm)

    set_tenant_id("t1")
    with pytest.raises(ValidationError):
        svc.handle_inbound({"message_id": "", "from_phone": "x", "text": "y"})
