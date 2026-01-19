from dataclasses import dataclass
from core.errors.base import AppError
from core.errors import domain as domain_errors


@dataclass(frozen=True)
class HttpErrorResponse:
    status_code: int
    body: dict


def to_http_error(err: Exception) -> HttpErrorResponse:
    # Erros do nosso domínio
    if isinstance(err, domain_errors.ValidationError):
        return HttpErrorResponse(400, {"error": err.code, "message": err.message, "meta": err.meta})
    if isinstance(err, domain_errors.UnauthorizedError):
        return HttpErrorResponse(401, {"error": err.code, "message": err.message, "meta": err.meta})
    if isinstance(err, domain_errors.ForbiddenError):
        return HttpErrorResponse(403, {"error": err.code, "message": err.message, "meta": err.meta})
    if isinstance(err, domain_errors.NotFoundError):
        return HttpErrorResponse(404, {"error": err.code, "message": err.message, "meta": err.meta})
    if isinstance(err, domain_errors.ConflictError):
        return HttpErrorResponse(409, {"error": err.code, "message": err.message, "meta": err.meta})

    # Erros base da app (fallback)
    if isinstance(err, AppError):
        return HttpErrorResponse(400, {"error": err.code, "message": err.message, "meta": err.meta})

    # Unknown/unhandled
    return HttpErrorResponse(500, {"error": "internal_error", "message": "Internal server error"})
