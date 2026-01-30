import os
import uuid

import pytest

from core.config import load_config
from core.tenancy import clear_tenant_id
from modules.tenants.repo.sql import SqlTenantRepo
from modules.tenants.service.tenant_service import TenantService
from modules.crm.models.customer import Customer
from modules.crm.repo.sql import SqlCrmRepo
from modules.messaging.models import Conversation, Message
from modules.messaging.repo.sql import SqlMessagingRepo


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader
    monkeypatch.setattr(loader, "_config", None)
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    yield
    monkeypatch.setattr(loader, "_config", None)
    clear_tenant_id()


def test_sql_repos_scope_by_tenant():
    load_config()
    tenant_service = TenantService(SqlTenantRepo())
    crm_repo = SqlCrmRepo()
    messaging_repo = SqlMessagingRepo()

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    tenant_service.create_tenant(tenant_a, "Tenant A")
    tenant_service.create_tenant(tenant_b, "Tenant B")

    customer_a = Customer.create(
        customer_id=str(uuid.uuid4()),
        tenant_id=tenant_a,
        name="Alice",
        phone="111",
    )
    customer_b = Customer.create(
        customer_id=str(uuid.uuid4()),
        tenant_id=tenant_b,
        name="Bob",
        phone="222",
    )
    crm_repo.create_customer(customer_a)
    crm_repo.create_customer(customer_b)

    conversation_a = Conversation.create(
        conversation_id=str(uuid.uuid4()),
        tenant_id=tenant_a,
        customer_id=customer_a.id,
        channel="whatsapp",
    )
    conversation_b = Conversation.create(
        conversation_id=str(uuid.uuid4()),
        tenant_id=tenant_b,
        customer_id=customer_b.id,
        channel="whatsapp",
    )
    messaging_repo.upsert_conversation(conversation_a)
    messaging_repo.upsert_conversation(conversation_b)

    message_a = Message.inbound(
        message_id=str(uuid.uuid4()),
        tenant_id=tenant_a,
        conversation_id=conversation_a.id,
        provider="meta",
        provider_message_id="m-1",
        from_phone="111",
        to_phone=None,
        body="Hi",
    )
    message_b = Message.inbound(
        message_id=str(uuid.uuid4()),
        tenant_id=tenant_b,
        conversation_id=conversation_b.id,
        provider="meta",
        provider_message_id="m-2",
        from_phone="222",
        to_phone=None,
        body="Hi",
    )
    messaging_repo.create_message(message_a)
    messaging_repo.create_message(message_b)

    assert len(crm_repo.list_customers(tenant_a)) == 1
    assert crm_repo.list_customers(tenant_a)[0].id == customer_a.id
    assert len(crm_repo.list_customers(tenant_b)) == 1
    assert crm_repo.list_customers(tenant_b)[0].id == customer_b.id

    assert messaging_repo.count_messages(tenant_id=tenant_a) == 1
    assert messaging_repo.count_messages(tenant_id=tenant_b) == 1
