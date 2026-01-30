import os
import uuid

import pytest

from core.config import load_config
from core.tenancy import clear_tenant_id, set_tenant_id
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.service import CrmService
from modules.messaging.repo.sql import SqlMessagingRepo
from modules.messaging.service import InboundWebhookService
from modules.messaging.models import WhatsAppAccount
from modules.tenants.repo.sql import SqlTenantRepo
from modules.tenants.service.tenant_service import TenantService
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService
from modules.billing.models import PlanTier
from tasks.workers.messaging.inbound_worker import process_inbound_webhook
from core.errors import ForbiddenError


@pytest.fixture(autouse=True)
def reset_config_singleton(monkeypatch):
    import core.config.loader as loader
    monkeypatch.setattr(loader, "_config", None)
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("APP_NAME", "beauty-crm")
    os.environ.setdefault("DATABASE_URL", "dev")
    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("TENANT_HEADER", "X-Tenant-ID")
    yield
    monkeypatch.setattr(loader, "_config", None)
    clear_tenant_id()


def _setup_dependencies():
    load_config()
    tenant_id = str(uuid.uuid4())

    tenant_service = TenantService(SqlTenantRepo())
    tenant_service.create_tenant(tenant_id, name="Tenant")

    messaging_repo = SqlMessagingRepo()
    account = WhatsAppAccount.create(
        account_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        provider="meta",
        phone_number_id="pn-123",
    )
    messaging_repo.create_whatsapp_account(account)

    billing = BillingService(InMemoryBillingRepo())
    crm_repo = InMemoryCrmRepo()
    crm = CrmService(crm_repo, billing)
    return tenant_id, messaging_repo, crm, billing


def test_inbound_worker_blocks_whatsapp_when_plan_disabled():
    tenant_id, messaging_repo, crm, billing = _setup_dependencies()
    billing.set_plan(tier=PlanTier.STARTER)

    set_tenant_id(tenant_id)
    crm.create_customer(name="Bea", phone="351111")

    inbound_service = InboundWebhookService(messaging_repo, crm, billing)

    with pytest.raises(ForbiddenError):
        process_inbound_webhook(
            inbound_service=inbound_service,
            payload={
                "provider": "meta",
                "external_event_id": "evt-1",
                "phone_number_id": "pn-123",
                "message_id": "m-1",
                "from_phone": "351111",
                "text": "Oi",
            },
            signature_valid=True,
        )


def test_inbound_worker_accepts_whatsapp_when_plan_enabled():
    tenant_id, messaging_repo, crm, billing = _setup_dependencies()
    billing.set_plan(tier=PlanTier.PRO)

    set_tenant_id(tenant_id)
    crm.create_customer(name="Bea", phone="351111")

    inbound_service = InboundWebhookService(messaging_repo, crm, billing)

    res = process_inbound_webhook(
        inbound_service=inbound_service,
        payload={
            "provider": "meta",
            "external_event_id": "evt-1",
            "phone_number_id": "pn-123",
            "message_id": "m-1",
            "from_phone": "351111",
            "text": "Oi",
        },
        signature_valid=True,
    )
    assert res["status"] == "processed"
    assert messaging_repo.count_messages(tenant_id=tenant_id) == 1
