from core.errors import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    to_http_error,
    from_http_exception,
)

def test_validation_error_maps_to_400():
    res = to_http_error(ValidationError("bad input", meta={"field": "name"}))
    assert res.status_code == 400
    assert res.body["error"] == "VALIDATION_ERROR"
    assert res.body["details"]["field"] == "name"

def test_not_found_maps_to_404():
    res = to_http_error(NotFoundError())
    assert res.status_code == 404
    assert res.body["error"] == "NOT_FOUND"

def test_conflict_maps_to_409():
    res = to_http_error(ConflictError())
    assert res.status_code == 409
    assert res.body["error"] == "CONFLICT"

def test_unauthorized_maps_to_401():
    res = to_http_error(UnauthorizedError())
    assert res.status_code == 401
    assert res.body["error"] == "UNAUTHORIZED"

def test_forbidden_maps_to_403():
    res = to_http_error(ForbiddenError())
    assert res.status_code == 403
    assert res.body["error"] == "FORBIDDEN"

def test_unknown_exception_maps_to_500():
    res = to_http_error(Exception("boom"))
    assert res.status_code == 500
    assert res.body["error"] == "INTERNAL_ERROR"


def test_http_exception_normalizes_validation_shape():
    res = from_http_exception(status_code=400, detail="invalid payload")
    assert res.status_code == 400
    assert res.body["error"] == "VALIDATION_ERROR"
    assert res.body["details"]["message"] == "invalid payload"


def test_http_exception_preserves_preformatted_body():
    preformatted = {"error": "APPOINTMENT_OVERLAP", "conflicts": [{"id": "1"}]}
    res = from_http_exception(status_code=409, detail=preformatted)
    assert res.status_code == 409
    assert res.body == preformatted
