from dataclasses import dataclass
from modules.billing.models.plans import PlanTier


@dataclass(frozen=True)
class UsageMetric:
    current: int
    max: int | None  # None = unlimited


@dataclass(frozen=True)
class PlanStatus:
    tenant_id: str
    tier: PlanTier
    active: bool

    whatsapp_enabled: bool
    automations_enabled: bool

    users: UsageMetric
    customers: UsageMetric
    automations: UsageMetric
