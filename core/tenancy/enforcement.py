from core.tenancy.context import get_tenant_id


def require_tenant_id() -> str:
    tenant_id = get_tenant_id()
    if tenant_id is None:
        raise RuntimeError("Missing tenant context (tenant_id not set)")
    return tenant_id
