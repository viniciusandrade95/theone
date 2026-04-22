from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.http.deps import require_tenant_header, require_user_or_assistant_connector
from app.http.routes.assistant_prebook import _ensure_tz, _parse_requested_date_time, _resolve_default_location
from core.db.session import db_session
from core.errors import ForbiddenError, ValidationError
from core.observability.logging import log_event
from core.observability.tracing import require_trace_id
from core.tenancy import require_tenant_id
from modules.crm.models.appointment_orm import AppointmentORM
from modules.crm.models.location_orm import LocationORM
from modules.crm.models.service_orm import ServiceORM
from modules.crm.repo_appointments import AppointmentOverlapError, AppointmentsRepo


router = APIRouter(prefix="/internal/chatbot/workflows")


class ChatbotWorkflowOperationIn(BaseModel):
    tenant_id: str | None = None
    client_id: str | None = None
    session_id: str | None = None
    trace_id: str | None = None
    idempotency_key: str | None = None
    workflow_name: str | None = None
    operation: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    operation_hints: dict[str, Any] = Field(default_factory=dict)


def _operation_result(
    *,
    ok: bool,
    message: str,
    reference: str = "unavailable",
    mode: str,
    request_kind: str,
    operational_status: str,
    error_code: str | None = None,
    retriable: bool = False,
    human_confirmation_required: bool = False,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "reference": reference,
        "mode": mode,
        "message": message,
        "request_kind": request_kind,
        "error_code": error_code,
        "retriable": retriable,
        "human_confirmation_required": human_confirmation_required,
        "operational_status": operational_status,
        "data": data or {},
    }


def _validate_operation_context(payload: ChatbotWorkflowOperationIn, *, expected_operation: str) -> str:
    tenant_id = require_tenant_id()
    body_tenant = (payload.tenant_id or payload.client_id or "").strip()
    if body_tenant and body_tenant != tenant_id:
        raise ForbiddenError("tenant_mismatch", meta={"header": tenant_id, "body": body_tenant})
    operation = (payload.operation or expected_operation).strip()
    if operation != expected_operation:
        raise ValidationError(
            "operation_mismatch",
            meta={"expected": expected_operation, "received": operation},
        )
    return tenant_id


def _appointment_reference(appointment_id: uuid.UUID, *, prefix: str = "RS") -> str:
    return f"{prefix}-{appointment_id.hex[:8].upper()}"


def _parse_uuid(value: Any) -> uuid.UUID | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def _parse_local_start(*, payload: dict[str, Any], location: LocationORM) -> datetime:
    requested_date = str(payload.get("new_date") or payload.get("date") or "").strip()
    requested_time = str(payload.get("new_time") or payload.get("time") or "").strip()
    if not requested_date or not requested_time:
        raise ValidationError(
            "missing_reschedule_date_time",
            meta={"required": ["new_date", "new_time"]},
        )
    parsed_date, parsed_time = _parse_requested_date_time(
        requested_date=requested_date,
        requested_time=requested_time,
    )
    tz_name = str(payload.get("timezone") or "").strip() or location.timezone
    tz = _ensure_tz(tz_name)
    return datetime.combine(parsed_date, parsed_time, tzinfo=tz).astimezone(timezone.utc)


def _duration_for(appointment: AppointmentORM, service: ServiceORM | None) -> timedelta:
    existing_duration = appointment.ends_at - appointment.starts_at
    if existing_duration.total_seconds() > 0:
        return existing_duration
    if service is not None and service.duration_minutes:
        return timedelta(minutes=int(service.duration_minutes))
    return timedelta(minutes=30)


def _appointment_service(session, *, tenant_uuid: uuid.UUID, appointment: AppointmentORM) -> ServiceORM | None:
    if appointment.service_id is None:
        return None
    return session.execute(
        select(ServiceORM)
        .where(ServiceORM.tenant_id == tenant_uuid)
        .where(ServiceORM.id == appointment.service_id)
        .where(ServiceORM.deleted_at.is_(None))
    ).scalar_one_or_none()


def _resolve_target_appointment(
    session,
    *,
    tenant_uuid: uuid.UUID,
    payload: dict[str, Any],
) -> tuple[AppointmentORM | None, str | None]:
    explicit_id = _parse_uuid(payload.get("appointment_id")) or _parse_uuid(payload.get("booking_ref"))
    if explicit_id is not None:
        appointment = session.execute(
            select(AppointmentORM)
            .where(AppointmentORM.tenant_id == tenant_uuid)
            .where(AppointmentORM.id == explicit_id)
            .where(AppointmentORM.deleted_at.is_(None))
            .where(AppointmentORM.status != "cancelled")
        ).scalar_one_or_none()
        return appointment, "appointment_not_found" if appointment is None else None

    old_date = str(payload.get("old_date") or "").strip()
    if old_date:
        location = _resolve_default_location(session, tenant_id=str(tenant_uuid))
        parsed_date, _ = _parse_requested_date_time(requested_date=old_date, requested_time="00:00")
        tz = _ensure_tz(location.timezone)
        start = datetime.combine(parsed_date, datetime.min.time(), tzinfo=tz).astimezone(timezone.utc)
        end = start + timedelta(days=1)
        candidates = list(
            session.execute(
                select(AppointmentORM)
                .where(AppointmentORM.tenant_id == tenant_uuid)
                .where(AppointmentORM.deleted_at.is_(None))
                .where(AppointmentORM.status == "booked")
                .where(AppointmentORM.starts_at >= start)
                .where(AppointmentORM.starts_at < end)
                .order_by(AppointmentORM.starts_at.asc(), AppointmentORM.id.asc())
            )
            .scalars()
            .all()
        )
        if len(candidates) == 1:
            return candidates[0], None
        if len(candidates) > 1:
            return None, "appointment_ambiguous"
        return None, "appointment_not_found"

    customer_id = _parse_uuid(payload.get("customer_id"))
    service_id = _parse_uuid(payload.get("service_id"))
    stmt = (
        select(AppointmentORM)
        .where(AppointmentORM.tenant_id == tenant_uuid)
        .where(AppointmentORM.deleted_at.is_(None))
        .where(AppointmentORM.status == "booked")
        .where(AppointmentORM.starts_at >= datetime.now(timezone.utc))
        .order_by(AppointmentORM.starts_at.asc(), AppointmentORM.id.asc())
        .limit(2)
    )
    if customer_id is not None:
        stmt = stmt.where(AppointmentORM.customer_id == customer_id)
    if service_id is not None:
        stmt = stmt.where(AppointmentORM.service_id == service_id)
    candidates = list(session.execute(stmt).scalars().all())
    if len(candidates) == 1:
        return candidates[0], None
    if len(candidates) > 1:
        return None, "appointment_ambiguous"
    return None, "appointment_not_found"


def _reschedule_failure_for(reason: str | None) -> dict[str, Any]:
    if reason == "appointment_ambiguous":
        return _operation_result(
            ok=False,
            mode="reschedule_validation",
            request_kind="reschedule_request",
            operational_status="validation_error",
            error_code="appointment_ambiguous",
            message="Encontrei mais de um agendamento possível. Informe a referência ou horário do agendamento que deseja remarcar.",
            human_confirmation_required=False,
        )
    if reason == "appointment_not_found":
        return _operation_result(
            ok=False,
            mode="reschedule_validation",
            request_kind="reschedule_request",
            operational_status="validation_error",
            error_code="appointment_not_found",
            message=(
                "Não consegui confirmar a remarcação porque não encontrei esse agendamento. "
                "Confira a referência ou a data do agendamento."
            ),
            human_confirmation_required=False,
        )
    return _operation_result(
        ok=False,
        mode="reschedule_validation",
        request_kind="reschedule_request",
        operational_status="validation_error",
        error_code="appointment_target_required",
        message="Preciso saber qual agendamento você quer remarcar. Informe a referência ou a data atual do agendamento.",
        human_confirmation_required=False,
    )


def _available_windows(
    repo: AppointmentsRepo,
    *,
    tenant_uuid: uuid.UUID,
    location_id: uuid.UUID,
    requested_start: datetime,
    duration: timedelta,
    exclude_appointment_id: uuid.UUID,
    limit: int = 3,
) -> list[dict[str, str]]:
    windows: list[dict[str, str]] = []
    for offset_minutes in (30, 60, 90, 120, 150, 180):
        candidate_start = requested_start + timedelta(minutes=offset_minutes)
        candidate_end = candidate_start + duration
        conflicts = repo._find_overlaps(
            tenant_id=tenant_uuid,
            location_id=location_id,
            starts_at=candidate_start,
            ends_at=candidate_end,
            exclude_appointment_id=exclude_appointment_id,
        )
        if conflicts:
            continue
        windows.append(
            {
                "label": candidate_start.strftime("%H:%M"),
                "starts_at": candidate_start.isoformat(),
                "ends_at": candidate_end.isoformat(),
            }
        )
        if len(windows) >= limit:
            break
    return windows


@router.post("/availability-lookup")
def lookup_availability(
    payload: ChatbotWorkflowOperationIn,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _tenant=Depends(require_tenant_header),
    _auth=Depends(require_user_or_assistant_connector),
):
    tenant_id = _validate_operation_context(payload, expected_operation="lookup_availability")
    trace_id = require_trace_id()
    tenant_uuid = uuid.UUID(tenant_id)
    operation_payload = dict(payload.payload or {})

    with db_session() as session:
        request.app.state.container.tenant_service.get_or_fail(tenant_id)
        appointment, reason = _resolve_target_appointment(session, tenant_uuid=tenant_uuid, payload=operation_payload)
        if appointment is None:
            failure = _reschedule_failure_for(reason)
            return {**failure, "windows": []}

        location = session.execute(
            select(LocationORM)
            .where(LocationORM.tenant_id == tenant_uuid)
            .where(LocationORM.id == appointment.location_id)
            .where(LocationORM.deleted_at.is_(None))
            .where(LocationORM.is_active.is_(True))
        ).scalar_one_or_none()
        if location is None:
            raise ValidationError("location_not_found", meta={"location_id": str(appointment.location_id)})

        service = _appointment_service(session, tenant_uuid=tenant_uuid, appointment=appointment)
        requested_start = _parse_local_start(payload=operation_payload, location=location)
        duration = _duration_for(appointment, service)
        requested_end = requested_start + duration
        repo = AppointmentsRepo(session)
        conflicts = repo._find_overlaps(
            tenant_id=tenant_uuid,
            location_id=appointment.location_id,
            starts_at=requested_start,
            ends_at=requested_end,
            exclude_appointment_id=appointment.id,
        )
        if not conflicts:
            return {
                "ok": True,
                "message": "Horário disponível.",
                "operational_status": "ok",
                "windows": [
                    {
                        "label": requested_start.strftime("%H:%M"),
                        "starts_at": requested_start.isoformat(),
                        "ends_at": requested_end.isoformat(),
                    }
                ],
                "trace_id": trace_id,
                "idempotency_key": idempotency_key or payload.idempotency_key,
            }

        alternatives = _available_windows(
            repo,
            tenant_uuid=tenant_uuid,
            location_id=appointment.location_id,
            requested_start=requested_start,
            duration=duration,
            exclude_appointment_id=appointment.id,
        )
        return {
            "ok": True,
            "message": "Horário indisponível. Sugeri alternativas próximas.",
            "operational_status": "ok",
            "windows": alternatives,
            "conflicts": [str(item.id) for item in conflicts],
            "trace_id": trace_id,
            "idempotency_key": idempotency_key or payload.idempotency_key,
        }


@router.post("/reschedule-request")
def reschedule_request(
    payload: ChatbotWorkflowOperationIn,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    _tenant=Depends(require_tenant_header),
    _auth=Depends(require_user_or_assistant_connector),
):
    tenant_id = _validate_operation_context(payload, expected_operation="reschedule_request")
    trace_id = require_trace_id()
    tenant_uuid = uuid.UUID(tenant_id)
    operation_payload = dict(payload.payload or {})

    with db_session() as session:
        request.app.state.container.tenant_service.get_or_fail(tenant_id)
        appointment, reason = _resolve_target_appointment(session, tenant_uuid=tenant_uuid, payload=operation_payload)
        if appointment is None:
            return _reschedule_failure_for(reason)

        location = session.execute(
            select(LocationORM)
            .where(LocationORM.tenant_id == tenant_uuid)
            .where(LocationORM.id == appointment.location_id)
            .where(LocationORM.deleted_at.is_(None))
            .where(LocationORM.is_active.is_(True))
        ).scalar_one_or_none()
        if location is None:
            raise ValidationError("location_not_found", meta={"location_id": str(appointment.location_id)})

        service = _appointment_service(session, tenant_uuid=tenant_uuid, appointment=appointment)
        starts_at = _parse_local_start(payload=operation_payload, location=location)
        duration = _duration_for(appointment, service)
        ends_at = starts_at + duration
        repo = AppointmentsRepo(session)
        previous_starts_at = appointment.starts_at
        previous_ends_at = appointment.ends_at
        try:
            updated = repo.update(
                tenant_id=tenant_uuid,
                appointment_id=appointment.id,
                fields={
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                    "updated_by_user_id": None,
                },
            )
        except AppointmentOverlapError as err:
            return _operation_result(
                ok=False,
                reference=_appointment_reference(appointment.id),
                mode="reschedule_conflict",
                request_kind="reschedule_request",
                operational_status="conflict",
                error_code="appointment_overlap",
                message="Esse horário não está disponível para remarcação.",
                human_confirmation_required=False,
                data={"conflicts": err.conflicts},
            )

        reference = _appointment_reference(updated.id)
        log_event(
            "assistant_reschedule_completed",
            tenant_id=tenant_id,
            trace_id=trace_id,
            appointment_id=str(updated.id),
            idempotency_key=idempotency_key or payload.idempotency_key,
        )
        return _operation_result(
            ok=True,
            reference=reference,
            mode="reschedule",
            request_kind="reschedule_request",
            operational_status="ok",
            message=f"Remarcação confirmada para {starts_at.strftime('%d/%m/%Y')} às {starts_at.strftime('%H:%M')}.",
            human_confirmation_required=False,
            data={
                "appointment_id": str(updated.id),
                "starts_at": updated.starts_at.isoformat(),
                "ends_at": updated.ends_at.isoformat(),
                "previous_starts_at": previous_starts_at.isoformat(),
                "previous_ends_at": previous_ends_at.isoformat(),
                "trace_id": trace_id,
                "idempotency_key": idempotency_key or payload.idempotency_key,
                "reference": reference,
            },
        )
