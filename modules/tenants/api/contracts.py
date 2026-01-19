"""
API Contracts (framework-agnostic).

Quando integrarmos web framework, estes contratos serão usados em routes/controllers.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateTenantRequest:
    tenant_id: str
    name: str


@dataclass(frozen=True)
class TenantResponse:
    id: str
    name: str
    created_at: str
