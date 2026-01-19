from datetime import datetime, timedelta, timezone
from core.tenancy import set_tenant_id, clear_tenant_id
from modules.crm.repo import InMemoryCrmRepo
from modules.crm.service import CrmService
from modules.crm.models import PipelineStage
from modules.analytics.repo import InMemoryAnalyticsRepo
from modules.analytics.service import AnalyticsService
from modules.billing.repo import InMemoryBillingRepo
from modules.billing.service import BillingService

def test_analytics_summary_basic_flow():
    clear_tenant_id()

    billing = BillingService(InMemoryBillingRepo())

    # Setup CRM
    crm_repo = InMemoryCrmRepo()
    crm = CrmService(crm_repo, billing)

    # Setup Analytics
    analytics_repo = InMemoryAnalyticsRepo(crm_repo)
    analytics = AnalyticsService(analytics_repo)

    set_tenant_id("t1")

    # Create customers
    c1 = crm.create_customer(name="A")  # LEAD
    c2 = crm.create_customer(name="B")
    crm.move_stage(customer_id=c2.id, to_stage=PipelineStage.BOOKED)

    c3 = crm.create_customer(name="C")
    crm.move_stage(customer_id=c3.id, to_stage=PipelineStage.BOOKED)
    crm.move_stage(customer_id=c3.id, to_stage=PipelineStage.COMPLETED)

    # Interactions (retention)
    crm.add_interaction(customer_id=c1.id, type="note", content="hi")
    crm.add_interaction(customer_id=c1.id, type="note", content="again")

    crm.add_interaction(customer_id=c3.id, type="whatsapp", content="oi")

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=1)
    end = now + timedelta(days=1)

    summary = analytics.summary(start=start, end=end)

    assert summary.new_customers == 3
    assert summary.leads == 1
    assert summary.booked == 1
    assert summary.completed == 1
    assert summary.retained_customers == 1
    assert summary.total_interactions == 3

    clear_tenant_id()
