import pytest
from core.errors import ForbiddenError
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService, Feature, assert_allowed
from modules.billing.models import PlanTier


@pytest.fixture(autouse=True)
def tenancy_context():
    clear_tenant_id()
    yield
    clear_tenant_id()


def test_default_plan_is_starter():
    repo = InMemoryBillingRepo()
    svc = BillingService(repo)

    set_tenant_id("t1")
    sub = svc.get_or_create_subscription()
    assert sub.tier == PlanTier.STARTER


def test_upgrade_to_pro_enables_whatsapp():
    repo = InMemoryBillingRepo()
    svc = BillingService(repo)

    set_tenant_id("t1")
    svc.set_plan(tier=PlanTier.PRO)

    res = svc.can_use_feature(Feature.WHATSAPP)
    assert res.allowed is True


def test_starter_blocks_whatsapp():
    repo = InMemoryBillingRepo()
    svc = BillingService(repo)

    set_tenant_id("t1")
    svc.set_plan(tier=PlanTier.STARTER)

    res = svc.can_use_feature(Feature.WHATSAPP)
    assert res.allowed is False

    with pytest.raises(ForbiddenError):
        assert_allowed(res)


def test_limits_customers_starter():
    repo = InMemoryBillingRepo()
    svc = BillingService(repo)

    set_tenant_id("t1")
    svc.set_plan(tier=PlanTier.STARTER)

    ok = svc.check_limit(kind="customers", current=200)
    assert ok.allowed is True

    bad = svc.check_limit(kind="customers", current=201)
    assert bad.allowed is False


def test_enterprise_is_unlimited():
    repo = InMemoryBillingRepo()
    svc = BillingService(repo)

    set_tenant_id("t1")
    svc.set_plan(tier=PlanTier.ENTERPRISE)

    res = svc.check_limit(kind="customers", current=999999)
    assert res.allowed is True
