import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Mapping

from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from core.auth import get_current_user_id
from modules.audit.models.audit_log_orm import AuditLogORM


def _coerce_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    return value


def snapshot_orm(
    orm_obj: Any,
    *,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> dict[str, Any] | None:
    if orm_obj is None:
        return None

    mapper = sa_inspect(orm_obj).mapper
    include_set = set(include) if include is not None else None
    exclude_set = set(exclude or [])

    data: dict[str, Any] = {}
    for attr in mapper.column_attrs:
        key = attr.key
        if include_set is not None and key not in include_set:
            continue
        if key in exclude_set:
            continue
        data[key] = _json_safe(getattr(orm_obj, key))
    return data


def record_audit_log(
    session: Session,
    *,
    tenant_id: str | uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: str | uuid.UUID,
    before: Mapping[str, Any] | None = None,
    after: Mapping[str, Any] | None = None,
    user_id: str | uuid.UUID | None = None,
) -> None:
    resolved_user_id = user_id if user_id is not None else get_current_user_id()
    row = AuditLogORM(
        tenant_id=_coerce_uuid(str(tenant_id)) or tenant_id,
        user_id=_coerce_uuid(str(resolved_user_id)) if resolved_user_id else None,
        action=action,
        entity_type=entity_type,
        entity_id=_coerce_uuid(str(entity_id)) or entity_id,
        before=_json_safe(before),
        after=_json_safe(after),
    )
    session.add(row)
