from dataclasses import dataclass


@dataclass(frozen=True)
class Tenant:
    id: str
    name: str
