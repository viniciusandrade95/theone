import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from core.config.loader import load_config

from app.http.main import create_app


POSTGRES_URL = os.getenv("DATABASE_URL", "")


def _is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgresql+psycopg")


@pytest.fixture(scope="session", autouse=True)
def ensure_running_on_postgres():
    """
    This integration test is ONLY meaningful on Postgres because it validates RLS.
    Skip if DATABASE_URL isn't a Postgres URL.
    """
    if not _is_postgres_url(POSTGRES_URL):
        pytest.skip("Postgres integration test skipped: DATABASE_URL is not Postgres")


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    """
    Ensure config reloads from environment for each test.
    """
    import core.config.loader as loader
    monkeypatch.setattr(loader, "_config", None)

    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")

    yield

    monkeypatch.setattr(loader, "_config", None)


@pytest.fixture(autouse=True)
def clean_db():
    """
    Truncate tables between tests so each run is isolated.
    Requires that Alembic migrations have already created the schema.
    """
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)

    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        # Order avoids FK issues; CASCADE handles dependencies safely.
        conn.execute(text("TRUNCATE TABLE users, interactions, customers, tenants RESTART IDENTITY CASCADE"))

    yield
    engine.dispose()


def test_signup_sets_tenant_context_and_passes_rls():
    load_config()
    app = create_app()

    client = TestClient(app)

    email = f"{uuid.uuid4()}@example.com"

    # 1) Signup creates tenant + first user (this is where RLS used to break)
    resp = client.post(
        "/auth/signup",
        json={"tenant_name": "My Salon", "email": email, "password": "secret123"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "tenant_id" in body
    assert "token" in body
    assert body["email"] == email

    tenant_id = body["tenant_id"]
    token = body["token"]

    # 2) /auth/me should work with returned tenant_id + token
    me = client.get(
        "/auth/me",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200, me.text
    me_body = me.json()
    assert me_body["tenant_id"] == tenant_id
    assert me_body["email"] == email

    # 3) Prove tenant context is working by creating a customer (customers table has RLS)
    created = client.post(
        "/crm/customers",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        json={"name": "Maria", "phone": "351111", "tags": ["VIP"]},
    )
    assert created.status_code == 200, created.text
    customer_id = created.json()["id"]

    # 4) Fetch customer also passes RLS
    fetched = client.get(
        f"/crm/customers/{customer_id}",
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["name"] == "Maria"
