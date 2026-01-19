from core.tenancy import require_tenant_id
from collections.abc import Callable
from modules.billing.models import PLAN_CATALOG, PlanTier, Subscription, PlanStatus, UsageMetric
from modules.billing.repo.billing_repo import BillingRepo
from modules.billing.service.gates import Feature, GateResult, allow, deny


class BillingService:
    def __init__(
        self,
        repo: BillingRepo,
        *,
        count_users: Callable[[str], int] | None = None,
        count_customers: Callable[[str], int] | None = None,
        count_automations: Callable[[str], int] | None = None,
    ):
        self.repo = repo
        self.count_users = count_users or (lambda _tid: 0)
        self.count_customers = count_customers or (lambda _tid: 0)
        self.count_automations = count_automations or (lambda _tid: 0)


    def get_or_create_subscription(self) -> Subscription:
        tenant_id = require_tenant_id()
        sub = self.repo.get_subscription(tenant_id)
        if sub is None:
            sub = Subscription.create(tenant_id=tenant_id, tier=PlanTier.STARTER, active=True)
            self.repo.upsert_subscription(sub)
        return sub

    def set_plan(self, *, tier: PlanTier) -> Subscription:
        tenant_id = require_tenant_id()
        sub = self.repo.get_subscription(tenant_id)
        if sub is None:
            sub = Subscription.create(tenant_id=tenant_id, tier=tier, active=True)
        else:
            sub = sub.with_tier(tier)
        self.repo.upsert_subscription(sub)
        return sub

    def current_limits(self):
        sub = self.get_or_create_subscription()
        return PLAN_CATALOG[sub.tier]

    def can_use_feature(self, feature: Feature) -> GateResult:
        limits = self.current_limits()
        sub = self.get_or_create_subscription()

        if not sub.active:
            return deny("subscription_inactive")

        if feature == Feature.WHATSAPP:
            return allow() if limits.whatsapp_enabled else deny("whatsapp_not_in_plan")

        if feature == Feature.AUTOMATIONS:
            # automations enabled if max_automations > 0 or unlimited
            if limits.max_automations is None:
                return allow()
            return allow() if limits.max_automations > 0 else deny("automations_not_in_plan")

        return deny("unknown_feature")

    def check_limit(self, *, kind: str, current: int) -> GateResult:
        """
        kind: 'users' | 'customers' | 'automations'
        """
        limits = self.current_limits()

        if kind == "users":
            m = limits.max_users
        elif kind == "customers":
            m = limits.max_customers
        elif kind == "automations":
            m = limits.max_automations
        else:
            return deny("unknown_limit_kind")

        if m is None:
            return allow()
        return allow() if current <= m else deny(f"limit_exceeded:{kind}:{m}")


    def plan_status(self) -> PlanStatus:
        tenant_id = require_tenant_id()
        sub = self.get_or_create_subscription()
        limits = PLAN_CATALOG[sub.tier]

        users_current = self.count_users(tenant_id)
        customers_current = self.count_customers(tenant_id)
        automations_current = self.count_automations(tenant_id)

        whatsapp = self.can_use_feature(Feature.WHATSAPP).allowed
        automations = self.can_use_feature(Feature.AUTOMATIONS).allowed

        return PlanStatus(
            tenant_id=tenant_id,
            tier=sub.tier,
            active=sub.active,
            whatsapp_enabled=whatsapp,
            automations_enabled=automations,
            users=UsageMetric(current=users_current, max=limits.max_users),
            customers=UsageMetric(current=customers_current, max=limits.max_customers),
            automations=UsageMetric(current=automations_current, max=limits.max_automations),
        )

