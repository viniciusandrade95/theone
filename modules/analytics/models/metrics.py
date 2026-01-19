from dataclasses import dataclass

@dataclass(frozen=True)
class AnalyticsSummary:
    new_customers: int
    leads: int
    booked: int
    completed: int
    retained_customers: int
    total_interactions: int
