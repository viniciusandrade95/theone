import pytest
from core.tenancy import set_tenant_id, get_tenant_id, clear_tenant_id, require_tenant_id


def test_tenant_context_set_get_clear():
    clear_tenant_id()
    assert get_tenant_id() is None

    set_tenant_id("t1")
    assert get_tenant_id() == "t1"

    clear_tenant_id()
    assert get_tenant_id() is None


def test_set_tenant_rejects_empty():
    with pytest.raises(RuntimeError):
        set_tenant_id("")


def test_require_tenant_id_fails_if_missing():
    clear_tenant_id()
    with pytest.raises(RuntimeError) as e:
        require_tenant_id()
    assert "Missing tenant context" in str(e.value)


def test_require_tenant_id_returns_value():
    clear_tenant_id()
    set_tenant_id("tenant-123")
    assert require_tenant_id() == "tenant-123"
