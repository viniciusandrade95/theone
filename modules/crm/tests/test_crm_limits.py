import pytest
from core.errors import ForbiddenError
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.service import CrmService
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService


def test_customer_limit_starter_blocks_201st():
    clear_tenant_id()
    billing = BillingService(InMemoryBillingRepo())
    repo = InMemoryCrmRepo()
    crm = CrmService(repo, billing)

    set_tenant_id("t1")

    # cria 200 (limite do Starter)
    for i in range(200):
        crm.create_customer(name=f"C{i}")

    with pytest.raises(ForbiddenError):
        crm.create_customer(name="C201")

    clear_tenant_id()
