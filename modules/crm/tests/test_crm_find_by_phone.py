from core.tenancy import set_tenant_id, clear_tenant_id
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.service import CrmService
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService

def test_find_customer_by_phone():
    clear_tenant_id()
    repo = InMemoryCrmRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = CrmService(repo, billing)

    set_tenant_id("t1")
    c = svc.create_customer(name="Rita", phone="999")

    found = svc.find_customer_by_phone(phone="999")
    assert found is not None
    assert found.id == c.id

    clear_tenant_id()
