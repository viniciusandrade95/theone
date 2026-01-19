import pytest
from core.errors import NotFoundError, ValidationError
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.service import CrmService
from modules.crm.models import PipelineStage
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService

@pytest.fixture(autouse=True)
def tenancy_context():
    clear_tenant_id()
    yield
    clear_tenant_id()


def test_create_customer_and_get():
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = CrmService(repo, billing)

    set_tenant_id("t1")
    c = svc.create_customer(name="Maria", phone="123", email="maria@test.com", tags={"VIP"})
    fetched = svc.get_customer(customer_id=c.id)

    assert fetched.id == c.id
    assert fetched.tenant_id == "t1"
    assert "vip" in fetched.tags


def test_customer_is_isolated_by_tenant():
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = CrmService(repo, billing)

    set_tenant_id("t1")
    c = svc.create_customer(name="Joana")

    set_tenant_id("t2")
    with pytest.raises(NotFoundError):
        svc.get_customer(customer_id=c.id)


def test_add_and_list_interactions():
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = CrmService(repo, billing)

    set_tenant_id("t1")
    c = svc.create_customer(name="Ana")

    svc.add_interaction(customer_id=c.id, type="note", content="Primeiro contacto")
    svc.add_interaction(customer_id=c.id, type="whatsapp", content="Mensagem recebida")

    interactions = svc.list_interactions(customer_id=c.id)
    assert len(interactions) == 2
    assert interactions[0].customer_id == c.id


def test_pipeline_transitions_valid_and_invalid():
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = CrmService(repo, billing)

    set_tenant_id("t1")
    c = svc.create_customer(name="Carla")

    # LEAD -> BOOKED OK
    c2 = svc.move_stage(customer_id=c.id, to_stage=PipelineStage.BOOKED)
    assert c2.stage == PipelineStage.BOOKED

    # BOOKED -> LEAD invalid
    with pytest.raises(ValidationError):
        svc.move_stage(customer_id=c.id, to_stage=PipelineStage.LEAD)

    # BOOKED -> COMPLETED OK
    c3 = svc.move_stage(customer_id=c.id, to_stage=PipelineStage.COMPLETED)
    assert c3.stage == PipelineStage.COMPLETED

    # COMPLETED -> BOOKED invalid
    with pytest.raises(ValidationError):
        svc.move_stage(customer_id=c.id, to_stage=PipelineStage.BOOKED)
