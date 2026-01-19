import pytest
from core.errors import UnauthorizedError
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.iam.repo.in_memory import InMemoryUserRepo
from modules.iam.service.auth_service import AuthService
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService


@pytest.fixture(autouse=True)
def tenancy_context():
    clear_tenant_id()
    yield
    clear_tenant_id()


def test_register_and_authenticate_success():
    repo = InMemoryUserRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = AuthService(repo, billing)

    set_tenant_id("t1")
    user = svc.register(email="a@b.com", password="secret123")
    assert user.tenant_id == "t1"
    assert user.email == "a@b.com"

    authed = svc.authenticate(email="a@b.com", password="secret123")
    assert authed.id == user.id


def test_authenticate_wrong_password():
    repo = InMemoryUserRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = AuthService(repo, billing)

    set_tenant_id("t1")
    svc.register(email="a@b.com", password="secret123")

    with pytest.raises(UnauthorizedError):
        svc.authenticate(email="a@b.com", password="nope")


def test_authenticate_wrong_tenant_is_denied():
    repo = InMemoryUserRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = AuthService(repo, billing)

    set_tenant_id("t1")
    svc.register(email="a@b.com", password="secret123")

    set_tenant_id("t2")
    with pytest.raises(UnauthorizedError):
        svc.authenticate(email="a@b.com", password="secret123")


def test_missing_tenant_context_fails_fast():
    repo = InMemoryUserRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = AuthService(repo, billing)

    # sem set_tenant_id()
    with pytest.raises(RuntimeError):
        svc.register(email="a@b.com", password="secret123")

def test_user_limit_starter_blocks_second_user():
    repo = InMemoryUserRepo()
    billing = BillingService(InMemoryBillingRepo())
    svc = AuthService(repo, billing)

    set_tenant_id("t1")
    svc.register(email="a@b.com", password="secret123")

    with pytest.raises(Exception) as e:
        svc.register(email="c@d.com", password="secret123")

    # deve ser ForbiddenError (plan limit)
    assert e.value.__class__.__name__ == "ForbiddenError"

