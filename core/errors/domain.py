from dataclasses import dataclass
from core.errors.base import AppError


@dataclass(frozen=True)
class ValidationError(AppError):
    def __init__(self, message: str, meta: dict | None = None):
        super().__init__(code="validation_error", message=message, meta=meta)


@dataclass(frozen=True)
class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", meta: dict | None = None):
        super().__init__(code="not_found", message=message, meta=meta)


@dataclass(frozen=True)
class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", meta: dict | None = None):
        super().__init__(code="conflict", message=message, meta=meta)


@dataclass(frozen=True)
class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", meta: dict | None = None):
        super().__init__(code="unauthorized", message=message, meta=meta)


@dataclass(frozen=True)
class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", meta: dict | None = None):
        super().__init__(code="forbidden", message=message, meta=meta)
