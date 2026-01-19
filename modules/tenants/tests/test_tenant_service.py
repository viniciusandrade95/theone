import pytest
from core.errors import ConflictError, NotFoundError, ValidationError
from modules.tenants.repo.in_memory import InMemoryTenantRepo
from modules.tenants.service.tenant_service import TenantService


def test_create_tenant_success():
    repo = InMemoryTenantRepo()
    svc = TenantService(repo)

    tenant = svc.create_tenant("t1", "Salon A")
    assert tenant.id == "t1"
    assert tenant.name == "Salon A"


def test_create_tenant_rejects_empty_name():
    repo = InMemoryTenantRepo()
    svc = TenantService(repo)

    with pytest.raises(ValidationError):
        svc.create_tenant("t1", "")


def test_create_tenant_conflict():
    repo = InMemoryTenantRepo()
    svc = TenantService(repo)

    svc.create_tenant("t1", "Salon A")
    with pytest.raises(ConflictError):
        svc.create_tenant("t1", "Salon A again")


def test_get_tenant_not_found():
    repo = InMemoryTenantRepo()
    svc = TenantService(repo)

    with pytest.raises(NotFoundError):
        svc.get_tenant("missing")
