import os

import pytest
from sqlalchemy import inspect

from core.config import load_config
from core.db.session import db_session


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader
    monkeypatch.setattr(loader, "_config", None)
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "suicapp")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    yield
    monkeypatch.setattr(loader, "_config", None)


def _get_inspector():
    load_config()
    with db_session() as session:
        return inspect(session.get_bind())


def test_customer_unique_constraints():
    inspector = _get_inspector()
    constraints = inspector.get_unique_constraints("customers")
    columns = {tuple(sorted(c["column_names"])) for c in constraints}
    assert ("phone", "tenant_id") in columns
    assert ("email", "tenant_id") in columns


def test_crm_foreign_keys():
    inspector = _get_inspector()

    customer_fks = inspector.get_foreign_keys("customers")
    assert any(
        fk["referred_table"] == "tenants" and fk["constrained_columns"] == ["tenant_id"]
        for fk in customer_fks
    )

    interaction_fks = inspector.get_foreign_keys("interactions")
    assert any(
        fk["referred_table"] == "tenants" and fk["constrained_columns"] == ["tenant_id"]
        for fk in interaction_fks
    )
    assert any(
        fk["referred_table"] == "customers" and fk["constrained_columns"] == ["customer_id"]
        for fk in interaction_fks
    )


def test_not_null_columns():
    inspector = _get_inspector()

    customer_columns = {col["name"]: col["nullable"] for col in inspector.get_columns("customers")}
    assert customer_columns["tenant_id"] is False
    assert customer_columns["name"] is False
    assert customer_columns["tags"] is False
    assert customer_columns["consent_marketing"] is False
    assert customer_columns["stage"] is False
    assert customer_columns["created_at"] is False

    interaction_columns = {col["name"]: col["nullable"] for col in inspector.get_columns("interactions")}
    assert interaction_columns["tenant_id"] is False
    assert interaction_columns["customer_id"] is False
    assert interaction_columns["type"] is False
    assert interaction_columns["content"] is False
    assert interaction_columns["created_at"] is False
