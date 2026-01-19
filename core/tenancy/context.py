from contextvars import ContextVar

_tenant_id: ContextVar[str | None] = ContextVar("tenant_id", default=None)


def set_tenant_id(tenant_id: str):
    if not tenant_id or tenant_id.strip() == "":
        raise RuntimeError("tenant_id cannot be empty")
    _tenant_id.set(tenant_id)


def get_tenant_id() -> str | None:
    return _tenant_id.get()


def clear_tenant_id():
    _tenant_id.set(None)
