from dataclasses import dataclass
from enum import Enum


class PlanTier(str, Enum):
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class PlanLimits:
    max_users: int | None          # None = unlimited
    max_customers: int | None      # None = unlimited
    max_automations: int | None    # None = unlimited
    whatsapp_enabled: bool


PLAN_CATALOG: dict[PlanTier, PlanLimits] = {
    PlanTier.STARTER: PlanLimits(
        max_users=1,
        max_customers=200,
        max_automations=0,
        whatsapp_enabled=False,  # gated premium
    ),
    PlanTier.PRO: PlanLimits(
        max_users=5,
        max_customers=2000,
        max_automations=10,
        whatsapp_enabled=True,
    ),
    PlanTier.ENTERPRISE: PlanLimits(
        max_users=None,
        max_customers=None,
        max_automations=None,
        whatsapp_enabled=True,
    ),
}
