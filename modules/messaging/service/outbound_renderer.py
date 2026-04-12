import re
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.errors import ValidationError


ALLOWED_TEMPLATE_TYPES: set[str] = {
    "booking_confirmation",
    "reminder_24h",
    "reminder_3h",
    "post_service_followup",
    "review_request",
    "reactivation",
    "simple_campaign",
    "tomorrow_open_slot",
    "internal_followup_support",
    # Assistant automation confirmations (MVP)
    "assistant_prebook_confirmation",
    "assistant_handoff_confirmation",
}

ALLOWED_CHANNELS: set[str] = {"whatsapp", "email"}

ALLOWED_VARIABLES: set[str] = {
    "customer_name",
    "appointment_date",
    "appointment_time",
    "service_name",
    "location_name",
    "business_name",
}

_VAR_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def normalize_type(value: str) -> str:
    t = (value or "").strip()
    if not t:
        raise ValidationError("type is required")
    if t not in ALLOWED_TEMPLATE_TYPES:
        raise ValidationError("invalid_template_type", meta={"received": t, "allowed": sorted(ALLOWED_TEMPLATE_TYPES)})
    return t


def normalize_channel(value: str) -> str:
    c = (value or "").strip().lower()
    if not c:
        raise ValidationError("channel is required")
    if c not in ALLOWED_CHANNELS:
        raise ValidationError("invalid_channel", meta={"received": c, "allowed": sorted(ALLOWED_CHANNELS)})
    return c


def extract_variables(body: str) -> set[str]:
    return {m.group(1) for m in _VAR_RE.finditer(body or "") if m.group(1)}


def validate_template_body(body: str) -> None:
    text = (body or "").strip()
    if not text:
        raise ValidationError("body is required")
    vars_used = extract_variables(text)
    unknown = sorted(v for v in vars_used if v not in ALLOWED_VARIABLES)
    if unknown:
        raise ValidationError("unknown_template_variables", meta={"unknown": unknown, "allowed": sorted(ALLOWED_VARIABLES)})


def validate_final_body(body: str, *, max_len: int = 2000) -> str:
    text = (body or "").strip()
    if not text:
        raise ValidationError("final_body is required")
    if len(text) > max_len:
        raise ValidationError("final_body_too_long", meta={"max_len": max_len})
    return text


def ensure_zoneinfo(tz_name: str | None) -> ZoneInfo:
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            pass
    return ZoneInfo("UTC")


def format_appointment_date_time(*, starts_at: datetime, tz: ZoneInfo) -> tuple[str, str]:
    dt = starts_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(tz)
    return local.date().isoformat(), local.strftime("%H:%M")


@dataclass(frozen=True)
class RenderResult:
    rendered_body: str
    variables_used: list[str]


def render_template(*, body: str, context: dict[str, str | None]) -> RenderResult:
    validate_template_body(body)
    used = sorted(extract_variables(body))
    missing = sorted(v for v in used if not (context.get(v) or "").strip())
    if missing:
        raise ValidationError(
            "missing_template_context",
            meta={
                "missing": missing,
                "hint": "Provide appointment_id for appointment_* variables, and ensure customer has name.",
            },
        )

    def repl(match: re.Match) -> str:
        key = match.group(1)
        value = context.get(key)
        return str(value or "")

    rendered = _VAR_RE.sub(repl, body).strip()
    if not rendered:
        raise ValidationError("rendered_body_empty")
    return RenderResult(rendered_body=rendered, variables_used=used)
