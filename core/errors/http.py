from dataclasses import dataclass
from typing import Any
from core.errors.base import AppError
from core.errors import domain as domain_errors


@dataclass(frozen=True)
class HttpErrorResponse:
    status_code: int
    body: dict


def _details(message: str | None = None, meta: dict | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if message:
        payload["message"] = message
    if meta:
        payload.update(meta)
    return payload


def _status_error_code(status_code: int) -> str:
    if status_code in {400, 422}:
        return "VALIDATION_ERROR"
    if status_code == 401:
        return "UNAUTHORIZED"
    if status_code == 403:
        return "FORBIDDEN"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT"
    return "INTERNAL_ERROR"


def from_http_exception(*, status_code: int, detail: Any) -> HttpErrorResponse:
    if isinstance(detail, dict):
        body = dict(detail)
        if "error" not in body:
            body = {"error": _status_error_code(status_code), "details": body}
        return HttpErrorResponse(status_code, body)

    code = _status_error_code(status_code)
    if code == "NOT_FOUND":
        return HttpErrorResponse(status_code, {"error": code})
    if code == "INTERNAL_ERROR":
        return HttpErrorResponse(status_code, {"error": code})
    return HttpErrorResponse(status_code, {"error": code, "details": _details(message=str(detail) if detail else None)})


def to_http_error(err: Exception) -> HttpErrorResponse:
    # Erros do nosso domínio
    if isinstance(err, domain_errors.ValidationError):
        return HttpErrorResponse(
            400,
            {
                "error": "VALIDATION_ERROR",
                "details": _details(message=err.message, meta=err.meta),
            },
        )
    if isinstance(err, domain_errors.UnauthorizedError):
        return HttpErrorResponse(
            401,
            {
                "error": "UNAUTHORIZED",
                "details": _details(message=err.message, meta=err.meta),
            },
        )
    if isinstance(err, domain_errors.ForbiddenError):
        return HttpErrorResponse(
            403,
            {
                "error": "FORBIDDEN",
                "details": _details(message=err.message, meta=err.meta),
            },
        )
    if isinstance(err, domain_errors.NotFoundError):
        return HttpErrorResponse(404, {"error": "NOT_FOUND"})
    if isinstance(err, domain_errors.ConflictError):
        return HttpErrorResponse(
            409,
            {
                "error": "CONFLICT",
                "details": _details(message=err.message, meta=err.meta),
            },
        )

    # Erros base da app (fallback)
    if isinstance(err, AppError):
        return HttpErrorResponse(
            400,
            {
                "error": "VALIDATION_ERROR",
                "details": _details(message=err.message, meta=err.meta),
            },
        )

    # Unknown/unhandled
    return HttpErrorResponse(500, {"error": "INTERNAL_ERROR"})
