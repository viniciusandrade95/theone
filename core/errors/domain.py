from dataclasses import dataclass
from core.errors.base import AppError


@dataclass
class ValidationError(AppError):
    def __init__(self, message: str, meta: dict | None = None):
        super().__init__(code="validation_error", message=message, meta=meta)


@dataclass
class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", meta: dict | None = None):
        super().__init__(code="not_found", message=message, meta=meta)


@dataclass
class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", meta: dict | None = None):
        super().__init__(code="conflict", message=message, meta=meta)


@dataclass
class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", meta: dict | None = None):
        super().__init__(code="unauthorized", message=message, meta=meta)


@dataclass
class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", meta: dict | None = None):
        super().__init__(code="forbidden", message=message, meta=meta)
