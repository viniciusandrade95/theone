from dataclasses import dataclass
from enum import Enum
from core.errors import ForbiddenError


class Feature(str, Enum):
    WHATSAPP = "whatsapp"
    AUTOMATIONS = "automations"


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str | None = None


def deny(reason: str) -> GateResult:
    return GateResult(allowed=False, reason=reason)


def allow() -> GateResult:
    return GateResult(allowed=True, reason=None)


def assert_allowed(result: GateResult) -> None:
    if not result.allowed:
        raise ForbiddenError("Feature not available in current plan", meta={"reason": result.reason})
