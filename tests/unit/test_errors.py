from core.errors import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    to_http_error,
)

def test_validation_error_maps_to_400():
    res = to_http_error(ValidationError("bad input", meta={"field": "name"}))
    assert res.status_code == 400
    assert res.body["error"] == "validation_error"

def test_not_found_maps_to_404():
    res = to_http_error(NotFoundError())
    assert res.status_code == 404

def test_conflict_maps_to_409():
    res = to_http_error(ConflictError())
    assert res.status_code == 409

def test_unauthorized_maps_to_401():
    res = to_http_error(UnauthorizedError())
    assert res.status_code == 401

def test_forbidden_maps_to_403():
    res = to_http_error(ForbiddenError())
    assert res.status_code == 403

def test_unknown_exception_maps_to_500():
    res = to_http_error(Exception("boom"))
    assert res.status_code == 500
    assert res.body["error"] == "internal_error"
