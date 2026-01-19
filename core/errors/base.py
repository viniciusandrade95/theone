from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppError(Exception):
    code: str
    message: str
    meta: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
