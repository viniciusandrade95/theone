import uuid
from core.errors import NotFoundError, ValidationError
from core.tenancy import require_tenant_id
from modules.crm.models import Customer, Interaction, PipelineStage
from modules.crm.repo.crm_repo import CrmRepo
from modules.billing.service import BillingService
from core.errors import ForbiddenError


_ALLOWED_TRANSITIONS = {
    PipelineStage.LEAD: {PipelineStage.BOOKED},
    PipelineStage.BOOKED: {PipelineStage.COMPLETED},
    PipelineStage.COMPLETED: set(),
}


class CrmService:
    def __init__(self, repo: CrmRepo, billing: BillingService):
        self.repo = repo
        self.billing = billing

    def create_customer(self, *, name: str, phone: str | None = None, email: str | None = None, tags: set[str] | None = None) -> Customer:
        tenant_id = require_tenant_id()
        current = len(self.repo.list_customers(tenant_id))
        res = self.billing.check_limit(kind="customers", current=current + 1)
        if not res.allowed:
            raise ForbiddenError("Plan limit exceeded", meta={"reason": res.reason})

        customer = Customer.create(
            customer_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            email=email,
            tags=tags or set(),
        )
        self.repo.create_customer(customer)
        return customer

    def get_customer(self, *, customer_id: str) -> Customer:
        tenant_id = require_tenant_id()
        customer = self.repo.get_customer(tenant_id, customer_id)
        if customer is None:
            raise NotFoundError("Customer not found", meta={"tenant_id": tenant_id, "customer_id": customer_id})
        return customer

    def set_tags(self, *, customer_id: str, tags: set[str]) -> Customer:
        customer = self.get_customer(customer_id=customer_id)
        updated = customer.with_tags(tags)
        self.repo.update_customer(updated)
        return updated

    def add_interaction(self, *, customer_id: str, type: str, content: str) -> Interaction:
        tenant_id = require_tenant_id()
        # garante que customer existe no tenant
        _ = self.get_customer(customer_id=customer_id)

        interaction = Interaction.create(
            interaction_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            customer_id=customer_id,
            type=type,
            content=content,
        )
        self.repo.add_interaction(interaction)
        return interaction

    def list_interactions(self, *, customer_id: str) -> list[Interaction]:
        tenant_id = require_tenant_id()
        _ = self.get_customer(customer_id=customer_id)
        return self.repo.list_interactions(tenant_id, customer_id)

    def move_stage(self, *, customer_id: str, to_stage: PipelineStage) -> Customer:
        customer = self.get_customer(customer_id=customer_id)
        allowed = _ALLOWED_TRANSITIONS.get(customer.stage, set())
        if to_stage not in allowed:
            raise ValidationError(
                "Invalid pipeline transition",
                meta={"from": customer.stage.value, "to": to_stage.value},
            )
        updated = customer.with_stage(to_stage)
        self.repo.update_customer(updated)
        return updated


######################## messsaging

    def find_customer_by_phone(self, *, phone: str) -> Customer | None:
        tenant_id = require_tenant_id()
        if not phone or phone.strip() == "":
            raise ValidationError("phone is required")
        return self.repo.find_customer_by_phone(tenant_id, phone.strip())
