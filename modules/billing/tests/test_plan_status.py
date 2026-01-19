import uuid
from core.tenancy import set_tenant_id, clear_tenant_id
from core.security.hashing import hash_password

from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService
from modules.billing.models import PlanTier

from modules.iam.repo.in_memory import InMemoryUserRepo
from modules.iam.models.user import User

from modules.crm.repo import InMemoryCrmRepo
from modules.crm.models.customer import Customer


def test_plan_status_reports_usage_and_features():
    clear_tenant_id()

    users_repo = InMemoryUserRepo()
    crm_repo = InMemoryCrmRepo()

    billing = BillingService(
        InMemoryBillingRepo(),
        count_users=users_repo.count_users,
        count_customers=crm_repo.count_customers,
    )

    set_tenant_id("t1")
    billing.set_plan(tier=PlanTier.PRO)

    # Seed 2 users
    users_repo.create(User.create(
        user_id=str(uuid.uuid4()),
        tenant_id="t1",
        email="a@b.com",
        password_hash=hash_password("x"),
    ))
    users_repo.create(User.create(
        user_id=str(uuid.uuid4()),
        tenant_id="t1",
        email="c@d.com",
        password_hash=hash_password("x"),
    ))

    # Seed 3 customers
    crm_repo.create_customer(Customer.create(customer_id="c1", tenant_id="t1", name="A", phone=None, email=None, tags=set()))
    crm_repo.create_customer(Customer.create(customer_id="c2", tenant_id="t1", name="B", phone=None, email=None, tags=set()))
    crm_repo.create_customer(Customer.create(customer_id="c3", tenant_id="t1", name="C", phone=None, email=None, tags=set()))

    status = billing.plan_status()

    assert status.tier == PlanTier.PRO
    assert status.active is True

    # PRO enables whatsapp + automations (>=1)
    assert status.whatsapp_enabled is True
    assert status.automations_enabled is True

    assert status.users.current == 2
    assert status.users.max == 5

    assert status.customers.current == 3
    assert status.customers.max == 2000
