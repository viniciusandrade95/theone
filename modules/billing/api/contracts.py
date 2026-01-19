from dataclasses import dataclass
from modules.billing.models.plans import PlanTier

@dataclass(frozen=True)
class SetPlanRequest:
    tier: PlanTier
