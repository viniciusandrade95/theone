#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("docs/test_runs/latest")
DEFAULT_SCENARIO_FILE = Path("docs/test_runs/scenarios/core_booking_scenarios.json")
DEFAULT_JUDGE_PROMPT = Path("docs/test_runs/judge_prompt.md")
DEFAULT_RETRY_BACKOFF_SECONDS = (2.0, 4.0)


@dataclass
class HttpResult:
    status_code: int
    body_text: str
    json_body: dict[str, Any] | None
    headers: dict[str, str]
    error: str | None = None
    attempts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AssertionResult:
    status: str
    reasons: list[str] = field(default_factory=list)


@dataclass
class StepSummary:
    conversation_id: str | None
    session_id: str | None
    status: str | None
    reply_text: str
    trace_id: str | None
    source: str | None
    route: str | None
    workflow: str | None
    workflow_status: str | None
    slots: dict[str, Any]
    action_result: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    return "_".join(part for part in safe.split("_") if part) or "scenario"


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    data = load_json_file(path)
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError(f"{path} must contain a non-empty scenarios list")
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            raise ValueError(f"scenario #{index + 1} must be an object")
        if not scenario.get("name"):
            raise ValueError(f"scenario #{index + 1} is missing name")
        if not isinstance(scenario.get("steps"), list) or not scenario["steps"]:
            raise ValueError(f"scenario {scenario.get('name')} must contain steps")
    return scenarios


def parse_json_object(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float = 30) -> HttpResult:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return HttpResult(
                status_code=response.status,
                body_text=raw,
                json_body=parse_json_object(raw),
                headers=dict(response.headers.items()),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return HttpResult(
            status_code=exc.code,
            body_text=raw,
            json_body=parse_json_object(raw),
            headers=dict(exc.headers.items()),
            error=f"HTTP {exc.code}",
        )
    except Exception as exc:
        return HttpResult(status_code=0, body_text="", json_body=None, headers={}, error=str(exc))


def is_transient_upstream_failure(http: HttpResult) -> bool:
    body = http.json_body
    if not isinstance(body, dict):
        return False
    details = body.get("details")
    if not isinstance(details, dict):
        return False
    return (
        body.get("error") == "VALIDATION_ERROR"
        and details.get("message") == "Chatbot service request failed"
        and int(details.get("status") or 0) == 502
    )


def post_json_with_retries(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    timeout: float = 30,
    retry_backoffs: tuple[float, ...] = DEFAULT_RETRY_BACKOFF_SECONDS,
    sleeper: Any = time.sleep,
) -> HttpResult:
    attempts: list[dict[str, Any]] = []
    for attempt_index in range(len(retry_backoffs) + 1):
        http = post_json(url, payload, headers, timeout=timeout)
        transient = is_transient_upstream_failure(http)
        attempts.append(
            {
                "attempt": attempt_index + 1,
                "status_code": http.status_code,
                "transient_upstream_failure": transient,
                "error": http.error,
                "body_excerpt": http.body_text[:500],
            }
        )
        if not transient or attempt_index >= len(retry_backoffs):
            http.attempts = attempts
            return http
        sleeper(retry_backoffs[attempt_index])
    raise RuntimeError("unreachable retry loop")


def get_json(url: str, headers: dict[str, str], timeout: float = 30) -> HttpResult:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return HttpResult(
                status_code=response.status,
                body_text=raw,
                json_body=parse_json_object(raw),
                headers=dict(response.headers.items()),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return HttpResult(
            status_code=exc.code,
            body_text=raw,
            json_body=parse_json_object(raw),
            headers=dict(exc.headers.items()),
            error=f"HTTP {exc.code}",
        )
    except Exception as exc:
        return HttpResult(status_code=0, body_text="", json_body=None, headers={}, error=str(exc))


def nested_get(data: dict[str, Any] | None, path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def extract_step_summary(body: dict[str, Any] | None) -> StepSummary:
    raw = nested_get(body, "meta.raw", {}) if body else {}
    workflow_result = raw.get("workflow_result") if isinstance(raw, dict) else None
    if not isinstance(workflow_result, dict):
        workflow_result = {}
    action_result = workflow_result.get("action_result")
    slots = workflow_result.get("slots")
    reply = body.get("reply") if isinstance(body, dict) else None
    reply_text = ""
    if isinstance(reply, dict):
        reply_text = str(reply.get("text") or "")
    elif isinstance(reply, str):
        reply_text = reply
    return StepSummary(
        conversation_id=body.get("conversation_id") if isinstance(body, dict) else None,
        session_id=body.get("session_id") if isinstance(body, dict) else None,
        status=body.get("status") if isinstance(body, dict) else None,
        reply_text=reply_text,
        trace_id=body.get("trace_id") if isinstance(body, dict) else None,
        source=nested_get(body, "meta.source"),
        route=raw.get("route") if isinstance(raw, dict) else None,
        workflow=raw.get("workflow") if isinstance(raw, dict) else None,
        workflow_status=workflow_result.get("status"),
        slots=slots if isinstance(slots, dict) else {},
        action_result=action_result if isinstance(action_result, dict) else {},
    )


def contains_casefold(text: str, needle: str) -> bool:
    return needle.casefold() in text.casefold()


def make_failure(category: str, message: str, *, step_index: int | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {"category": category, "message": message}
    if step_index is not None:
        record["step_index"] = step_index
    return record


def failure_message(record: dict[str, Any]) -> str:
    prefix = record.get("category", "failure")
    step = record.get("step_index")
    if step is None:
        return f"{prefix}: {record.get('message')}"
    return f"step {step}: {prefix}: {record.get('message')}"


def categorize_assertion_reason(reason: str, http: HttpResult) -> str:
    if is_transient_upstream_failure(http):
        return "upstream_runtime_failure"
    if reason.startswith("HTTP request failed") or reason == "response body is not a JSON object":
        return "upstream_runtime_failure"
    return "assertion_failure"


def final_verdict_from_failures(failure_records: list[dict[str, Any]]) -> str:
    if not failure_records:
        return "PASS"
    categories = {record.get("category") for record in failure_records}
    if categories and categories <= {"upstream_runtime_failure"}:
        return "PARTIAL"
    if categories and categories <= {"crm_verification_failure"}:
        return "PARTIAL"
    return "FAIL"


def evaluate_step(step: dict[str, Any], http: HttpResult, summary: StepSummary, allow_prebooking_stub: bool) -> AssertionResult:
    reasons: list[str] = []
    if http.status_code < 200 or http.status_code >= 300:
        reasons.append(f"HTTP request failed with status {http.status_code}: {http.body_text[:500]}")
    if http.json_body is None:
        reasons.append("response body is not a JSON object")
    if not allow_prebooking_stub and "prebooking_stub" in http.body_text:
        reasons.append("prebooking_stub appeared in a real-tenant scenario")

    expected_status = step.get("expected_status")
    if expected_status and summary.workflow_status != expected_status and summary.status != expected_status:
        reasons.append(f"expected status {expected_status}, got response={summary.status} workflow={summary.workflow_status}")

    expected_route = step.get("expected_route")
    if expected_route and summary.route != expected_route:
        reasons.append(f"expected route {expected_route}, got {summary.route}")

    expected_workflow = step.get("expected_workflow")
    if expected_workflow and summary.workflow != expected_workflow:
        reasons.append(f"expected workflow {expected_workflow}, got {summary.workflow}")

    for forbidden_workflow in step.get("expected_workflow_not") or step.get("forbidden_workflows") or []:
        if summary.workflow == forbidden_workflow:
            reasons.append(f"workflow must not be {forbidden_workflow}")

    for needle in step.get("expected_reply_contains") or []:
        if not contains_casefold(summary.reply_text, str(needle)):
            reasons.append(f"reply missing expected text: {needle}")

    contains_any = step.get("expected_reply_contains_any") or []
    if contains_any and not any(contains_casefold(summary.reply_text, str(needle)) for needle in contains_any):
        joined = ", ".join(str(needle) for needle in contains_any)
        reasons.append(f"reply missing any expected text: {joined}")

    for needle in step.get("expected_reply_not_contains") or []:
        if contains_casefold(summary.reply_text, str(needle)):
            reasons.append(f"reply contained forbidden text: {needle}")

    for slot_name in step.get("expected_slots_present") or []:
        value = summary.slots.get(slot_name)
        if value in (None, "", [], {}):
            reasons.append(f"expected slot {slot_name} to be present")

    expected_fields = step.get("expected_action_result_fields") or {}
    if not isinstance(expected_fields, dict):
        reasons.append("expected_action_result_fields must be an object")
    else:
        for field_name, expected_value in expected_fields.items():
            actual = nested_get(summary.action_result, field_name)
            if expected_value == "__present__":
                if actual in (None, "", [], {}):
                    reasons.append(f"expected action_result.{field_name} to be present")
            elif actual != expected_value:
                reasons.append(f"expected action_result.{field_name}={expected_value!r}, got {actual!r}")

    if step.get("expected_no_rag_reset"):
        if summary.route == "rag" and not step.get("allow_rag_detour"):
            reasons.append("unexpected RAG route")
        allows_empty_collection = bool(step.get("allow_empty_collecting_slots")) or expected_status == "collecting"
        if (
            summary.workflow == "book_appointment"
            and summary.workflow_status == "collecting"
            and not summary.slots
            and not allows_empty_collection
        ):
            reasons.append("workflow appears to have reset to collecting with empty slots")

    return AssertionResult(status="FAIL" if reasons else "PASS", reasons=reasons)


def verify_crm(base_url: str, tenant_id: str, token: str, expectation: dict[str, Any] | None) -> dict[str, Any]:
    if not expectation:
        return {"status": "SKIPPED", "reasons": ["no CRM verification configured"]}
    appointments = expectation.get("appointments")
    if not isinstance(appointments, dict):
        return {"status": "SKIPPED", "reasons": ["no appointments verification configured"]}

    from_dt = resolve_datetime_template(appointments.get("from_dt"))
    to_dt = resolve_datetime_template(appointments.get("to_dt"))
    if not from_dt or not to_dt:
        return {"status": "PARTIAL", "reasons": ["appointments verification requires from_dt and to_dt"]}

    query = urllib.parse.urlencode({"from_dt": from_dt, "to_dt": to_dt, "page": 1, "page_size": 100})
    url = f"{base_url.rstrip('/')}/crm/appointments?{query}"
    http = get_json(
        url,
        headers={"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"},
        timeout=float(appointments.get("timeout_seconds", 30)),
    )
    result: dict[str, Any] = {
        "status_code": http.status_code,
        "raw_body": http.body_text,
        "parsed_body": http.json_body,
        "reasons": [],
    }
    if http.status_code < 200 or http.status_code >= 300 or http.json_body is None:
        result["status"] = "FAIL"
        result["reasons"].append(f"CRM appointments query failed with status {http.status_code}")
        return result

    items = http.json_body.get("items")
    if not isinstance(items, list):
        result["status"] = "FAIL"
        result["reasons"].append("CRM appointments response missing items list")
        return result

    match = appointments.get("match") if isinstance(appointments.get("match"), dict) else {}
    specificity_reasons = crm_match_specificity_reasons(match, appointments)
    if specificity_reasons:
        result["status"] = "PARTIAL"
        result["reasons"].extend(specificity_reasons)
        result["matched"] = []
        result["total_items"] = len(items)
        return result

    recent_after = appointments.get("created_after") or appointments.get("recent_created_after")
    recent_within_seconds = appointments.get("recent_created_within_seconds")
    if recent_within_seconds and not recent_after:
        recent_after = (datetime.now(timezone.utc) - timedelta(seconds=float(recent_within_seconds))).isoformat()

    matched = [item for item in items if appointment_matches(item, match, recent_after=recent_after)]
    expect_created = bool(appointments.get("expect_created"))
    if expect_created and not matched:
        result["status"] = "FAIL"
        result["reasons"].append("expected matching appointment to exist")
    elif not expect_created and matched:
        result["status"] = "FAIL"
        result["reasons"].append("expected no matching appointment, but found one")
    elif expect_created and len(matched) > 1 and not appointments.get("allow_ambiguous_match"):
        result["status"] = "PARTIAL"
        result["reasons"].append(f"CRM verification matched {len(matched)} appointments; match is ambiguous")
    else:
        result["status"] = "PASS"
    result["matched"] = matched
    result["total_items"] = len(items)
    return result


def crm_match_specificity_reasons(match: dict[str, Any], appointments: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    has_time = any(key in match for key in ("starts_at", "start_time", "starts_at_contains"))
    has_service = any(key in match for key in ("service_id", "service_name", "service_name_contains"))
    has_recent = any(key in appointments for key in ("created_after", "recent_created_after", "recent_created_within_seconds"))
    if not has_time:
        reasons.append("CRM verification requires expected date/time, e.g. match.starts_at")
    if not has_service:
        reasons.append("CRM verification requires expected service_id or service_name")
    if not has_recent:
        reasons.append("CRM verification should include created_after/recent_created_within_seconds to avoid stale matches")
    return reasons


def appointment_matches(item: Any, match: dict[str, Any], *, recent_after: str | None = None) -> bool:
    if not isinstance(item, dict):
        return False
    if recent_after and not iso_at_or_after(item.get("created_at"), recent_after):
        return False
    for key, expected in match.items():
        if key == "start_time":
            starts_at = parse_iso_datetime(str(item.get("starts_at") or ""))
            if starts_at is None or starts_at.strftime("%H:%M") != str(expected):
                return False
            continue
        if key.endswith("_contains"):
            actual_key = key[: -len("_contains")]
            if not contains_casefold(str(item.get(actual_key) or ""), str(expected)):
                return False
        elif item.get(key) != expected:
            return False
    return True


def resolve_datetime_template(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    today = datetime.now(timezone.utc).date()
    templates = {
        "relative:today_start_utc": today,
        "relative:tomorrow_start_utc": today + timedelta(days=1),
        "relative:day_after_tomorrow_start_utc": today + timedelta(days=2),
    }
    target = templates.get(value)
    if target is None:
        return value
    return datetime(target.year, target.month, target.day, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def iso_at_or_after(value: Any, minimum: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    parsed_value = parse_iso_datetime(value)
    parsed_minimum = parse_iso_datetime(minimum)
    if parsed_value is None or parsed_minimum is None:
        return False
    return parsed_value >= parsed_minimum


def parse_iso_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def build_transcript(step_results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, step in enumerate(step_results, start=1):
        request = step.get("request") or {}
        summary = step.get("summary") or {}
        user_message = request.get("message", "")
        assistant_message = summary.get("reply_text", "")
        lines.append(f"Turn {index} user: {user_message}")
        lines.append(f"Turn {index} assistant: {assistant_message}")
    return "\n".join(lines)


def validate_judge_output(data: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for key in ["naturalness_score", "coherence_score", "task_effectiveness_score", "recovery_score"]:
        value = data.get(key)
        if not isinstance(value, int) or value < 1 or value > 5:
            reasons.append(f"{key} must be an integer from 1 to 5")
    for key in ["asks_correct_next_question", "stayed_on_task", "sounded_human_enough"]:
        if not isinstance(data.get(key), bool):
            reasons.append(f"{key} must be boolean")
    for key in ["major_issues", "minor_issues"]:
        value = data.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            reasons.append(f"{key} must be list[str]")
    if not isinstance(data.get("summary"), str) or not data.get("summary", "").strip():
        reasons.append("summary must be a non-empty string")
    return not reasons, reasons


def extract_json_from_text(text: str) -> dict[str, Any] | None:
    direct = parse_json_object(text.strip())
    if direct is not None:
        return direct
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return parse_json_object("\n".join(lines).strip())
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return parse_json_object(stripped[start : end + 1])
    return None


def run_judge(
    *,
    prompt_path: Path,
    scenario: dict[str, Any],
    transcript: str,
    deterministic_result: dict[str, Any],
    judge_model: str | None,
    judge_timeout: float,
) -> dict[str, Any]:
    prompt = prompt_path.read_text(encoding="utf-8")
    context = {
        "scenario_name": scenario.get("name"),
        "intended_user_goal": scenario.get("description"),
        "deterministic_verdict": deterministic_result.get("final_verdict"),
        "crm_verification": deterministic_result.get("crm_verification"),
        "guardrails_observed": deterministic_result.get("guardrails_observed", []),
    }
    input_text = json.dumps({"context": context, "transcript": transcript}, ensure_ascii=False, indent=2)
    try:
        llm_client_cls, settings_cls = load_existing_llm_client()
        previous_timeout = os.environ.get("LLM_TIMEOUT_S")
        os.environ["LLM_TIMEOUT_S"] = str(judge_timeout)
        try:
            settings = settings_cls.from_env()
            client = llm_client_cls(settings)
            raw = client.complete(
                input_text,
                model=judge_model,
                instructions=prompt,
                temperature=0,
                allow_missing_key_mock=False,
            )
        finally:
            if previous_timeout is None:
                os.environ.pop("LLM_TIMEOUT_S", None)
            else:
                os.environ["LLM_TIMEOUT_S"] = previous_timeout
        parsed = extract_json_from_text(raw)
        if parsed is None:
            return {"status": "FAILED", "error": "judge output was not JSON", "raw_output": raw}
        valid, reasons = validate_judge_output(parsed)
        if not valid:
            return {"status": "MALFORMED", "errors": reasons, "raw_output": raw, "parsed_output": parsed}
        return {"status": "PASS", "result": parsed, "raw_output": raw}
    except Exception as exc:
        return {"status": "FAILED", "error": str(exc)}


def load_existing_llm_client() -> tuple[Any, Any]:
    root = Path(__file__).resolve().parents[1]
    default_chatbot_repo = root.parent / "chatbot1"
    chatbot_repo = Path(os.environ.get("CHATBOT1_REPO", str(default_chatbot_repo))).resolve()
    if not chatbot_repo.exists():
        raise RuntimeError(f"chatbot1 repo not found at {chatbot_repo}; set CHATBOT1_REPO")
    sys.path.insert(0, str(chatbot_repo))
    from app.config import LLMClient, Settings  # type: ignore

    return LLMClient, Settings


def run_scenario(
    *,
    scenario: dict[str, Any],
    base_url: str,
    tenant_id: str,
    token: str,
    surface: str,
    trace_prefix: str,
    run_id: str,
    output_dir: Path,
    judge: bool,
    judge_model: str | None,
    judge_timeout: float,
    fail_fast: bool,
    prompt_path: Path,
    step_delay_seconds: float,
) -> dict[str, Any]:
    scenario_name = scenario["name"]
    scenario_run_id = f"{run_id}-{slugify(scenario_name)}"
    conversation_id = None
    session_id = None
    step_results: list[dict[str, Any]] = []
    failure_records: list[dict[str, Any]] = []
    allow_prebooking_stub = bool(scenario.get("allow_prebooking_stub"))
    url = f"{base_url.rstrip('/')}/api/chatbot/message"

    for index, step in enumerate(scenario["steps"], start=1):
        trace_id = f"{trace_prefix}-{scenario_run_id}-{index}"
        payload = {
            "message": step["user_message"],
            "surface": surface,
            "conversation_id": conversation_id,
            "session_id": session_id,
            "start_new": index == 1,
        }
        http = post_json_with_retries(
            url,
            payload,
            headers={
                "X-Tenant-ID": tenant_id,
                "Authorization": f"Bearer {token}",
                "X-Trace-Id": trace_id,
            },
            timeout=float(step.get("timeout_seconds", 30)),
        )
        summary = extract_step_summary(http.json_body)
        if summary.conversation_id:
            conversation_id = summary.conversation_id
        if summary.session_id:
            session_id = summary.session_id
        assertion = evaluate_step(step, http, summary, allow_prebooking_stub=allow_prebooking_stub)
        if assertion.status == "FAIL":
            failure_records.extend(
                [
                    make_failure(categorize_assertion_reason(reason, http), reason, step_index=index)
                    for reason in assertion.reasons
                ]
            )

        step_results.append(
            {
                "step_index": index,
                "trace_id": trace_id,
                "request": payload,
                "http": {
                    "status_code": http.status_code,
                    "headers": http.headers,
                    "body_text": http.body_text,
                    "error": http.error,
                    "attempts": http.attempts,
                },
                "raw_response": http.json_body,
                "summary": summary.__dict__,
                "assertions": assertion.__dict__,
            }
        )
        if fail_fast and failure_records:
            break
        if step_delay_seconds > 0 and index < len(scenario["steps"]):
            time.sleep(step_delay_seconds)

    crm_verification = verify_crm(base_url, tenant_id, token, scenario.get("crm_verification"))
    if crm_verification.get("status") in {"FAIL", "PARTIAL"}:
        failure_records.extend(
            [
                make_failure("crm_verification_failure", reason)
                for reason in crm_verification.get("reasons", [])
            ]
        )

    transcript = build_transcript(step_results)
    guardrails_observed = detect_guardrails(step_results)
    result = {
        "scenario_name": scenario_name,
        "scenario_run_id": scenario_run_id,
        "description": scenario.get("description"),
        "tags": scenario.get("tags", []),
        "started_at": utc_now(),
        "conversation_id": conversation_id,
        "session_id": session_id,
        "transcript": transcript,
        "steps": step_results,
        "crm_verification": crm_verification,
        "guardrails_observed": guardrails_observed,
        "failure_records": failure_records,
        "failures": [failure_message(record) for record in failure_records],
        "final_verdict": final_verdict_from_failures(failure_records),
    }
    if judge:
        result["judge"] = run_judge(
            prompt_path=prompt_path,
            scenario=scenario,
            transcript=transcript,
            deterministic_result=result,
            judge_model=judge_model,
            judge_timeout=judge_timeout,
        )
        if result["judge"].get("status") != "PASS" and result["final_verdict"] == "PASS":
            result["final_verdict"] = "PARTIAL"
    else:
        result["judge"] = {"status": "DISABLED"}

    write_scenario_outputs(output_dir, scenario_name, result)
    return result


def detect_guardrails(step_results: list[dict[str, Any]]) -> list[str]:
    observed: list[str] = []
    for step in step_results:
        text = str(nested_get(step, "summary.reply_text", "")).casefold()
        action = nested_get(step, "summary.action_result", {}) or {}
        if "nome" in text or action.get("pending_slot") == "customer_name":
            observed.append("customer_identity_missing")
        if "telefone" in text or action.get("pending_slot") == "customer_phone":
            observed.append("customer_phone_missing")
        if "conflito" in text or "indispon" in text or action.get("error_code") in {"APPOINTMENT_OVERLAP", "slot_unavailable"}:
            observed.append("conflict_or_unavailable")
    return sorted(set(observed))


def write_scenario_outputs(output_dir: Path, scenario_name: str, result: dict[str, Any]) -> None:
    scenario_dir = output_dir / "scenario_results"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(scenario_name)
    write_json(scenario_dir / f"{slug}.json", result)
    (scenario_dir / f"{slug}.md").write_text(render_scenario_markdown(result), encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def render_scenario_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['scenario_name']}",
        "",
        f"- Verdict: {result['final_verdict']}",
        f"- Conversation ID: {result.get('conversation_id')}",
        f"- Session ID: {result.get('session_id')}",
        f"- Judge: {nested_get(result, 'judge.status', 'DISABLED')}",
        "",
        "## Transcript",
        "",
        "```text",
        result.get("transcript", ""),
        "```",
        "",
        "## Failures",
        "",
    ]
    failures = result.get("failures") or []
    if failures:
        lines.extend([f"- {failure}" for failure in failures])
    else:
        lines.append("- None")
    lines.extend(["", "## CRM Verification", "", "```json", json.dumps(result.get("crm_verification"), ensure_ascii=False, indent=2), "```"])
    if result.get("judge", {}).get("status") not in {"DISABLED", None}:
        lines.extend(["", "## Judge", "", "```json", json.dumps(result.get("judge"), ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines) + "\n"


def summarize_run(
    *,
    run_id: str,
    started_at: str,
    base_url: str,
    tenant_id: str,
    judge_enabled: bool,
    scenario_results: list[dict[str, Any]],
) -> dict[str, Any]:
    verdict_counts = {"PASS": 0, "FAIL": 0, "PARTIAL": 0}
    failure_patterns: dict[str, dict[str, int]] = {
        "upstream_runtime_failure": {},
        "assertion_failure": {},
        "crm_verification_failure": {},
    }
    judge_issues: dict[str, int] = {}
    worst_scores: list[dict[str, Any]] = []
    for result in scenario_results:
        verdict = result.get("final_verdict", "PARTIAL")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        for record in result.get("failure_records") or []:
            category = str(record.get("category") or "assertion_failure")
            if category not in failure_patterns:
                failure_patterns[category] = {}
            key = str(record.get("message") or "")[:160]
            failure_patterns[category][key] = failure_patterns[category].get(key, 0) + 1
        judge_result = nested_get(result, "judge.result")
        if isinstance(judge_result, dict):
            scores = [
                judge_result.get("naturalness_score"),
                judge_result.get("coherence_score"),
                judge_result.get("task_effectiveness_score"),
                judge_result.get("recovery_score"),
            ]
            numeric_scores = [score for score in scores if isinstance(score, int)]
            if numeric_scores:
                worst_scores.append({"scenario": result["scenario_name"], "min_score": min(numeric_scores), "judge": judge_result})
            for issue in (judge_result.get("major_issues") or []) + (judge_result.get("minor_issues") or []):
                judge_issues[issue] = judge_issues.get(issue, 0) + 1

    return {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": utc_now(),
        "base_url": base_url,
        "tenant_id": tenant_id,
        "judge_enabled": judge_enabled,
        "total_scenarios": len(scenario_results),
        "pass_count": verdict_counts.get("PASS", 0),
        "fail_count": verdict_counts.get("FAIL", 0),
        "partial_count": verdict_counts.get("PARTIAL", 0),
        "common_failure_patterns": {
            category: sorted(
                [{"pattern": key, "count": count} for key, count in patterns.items()],
                key=lambda item: item["count"],
                reverse=True,
            )[:10]
            for category, patterns in failure_patterns.items()
        },
        "worst_conversational_scores": sorted(worst_scores, key=lambda item: item["min_score"])[:10],
        "top_judge_issues": sorted(
            [{"issue": key, "count": count} for key, count in judge_issues.items()],
            key=lambda item: item["count"],
            reverse=True,
        )[:10],
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Chatbot Hybrid Eval Summary",
        "",
        f"- Timestamp: {summary['started_at']}",
        f"- Base URL: {summary['base_url']}",
        f"- Tenant ID: {summary['tenant_id']}",
        f"- Judge: {'enabled' if summary['judge_enabled'] else 'disabled'}",
        f"- Total scenarios: {summary['total_scenarios']}",
        f"- Pass: {summary['pass_count']}",
        f"- Fail: {summary['fail_count']}",
        f"- Partial: {summary['partial_count']}",
        "",
        "## Upstream / Runtime Failures",
        "",
    ]
    patterns_by_category = summary.get("common_failure_patterns") or {}
    upstream = patterns_by_category.get("upstream_runtime_failure") or []
    product = patterns_by_category.get("assertion_failure") or []
    crm = patterns_by_category.get("crm_verification_failure") or []
    lines.extend([f"- {item['count']}x {item['pattern']}" for item in upstream] or ["- None"])
    lines.extend(["", "## Product Logic Failures", ""])
    lines.extend([f"- {item['count']}x {item['pattern']}" for item in product] or ["- None"])
    lines.extend(["", "## CRM Verification Failures", ""])
    lines.extend([f"- {item['count']}x {item['pattern']}" for item in crm] or ["- None"])
    lines.extend(["", "## Worst Conversational Scores", ""])
    scores = summary.get("worst_conversational_scores") or []
    lines.extend([f"- {item['scenario']}: min score {item['min_score']}" for item in scores] or ["- Judge disabled or no scores"])
    lines.extend(["", "## Top Judge Issues", ""])
    issues = summary.get("top_judge_issues") or []
    lines.extend([f"- {item['count']}x {item['issue']}" for item in issues] or ["- None"])
    return "\n".join(lines) + "\n"


def run_once(args: argparse.Namespace, output_dir: Path) -> dict[str, Any]:
    scenarios = load_scenarios(Path(args.scenario_file))
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    started_at = utc_now()
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        result = run_scenario(
            scenario=scenario,
            base_url=args.base_url,
            tenant_id=args.tenant_id,
            token=args.token,
            surface=args.surface,
            trace_prefix=args.trace_prefix,
            run_id=run_id,
            output_dir=output_dir,
            judge=args.judge,
            judge_model=args.judge_model,
            judge_timeout=args.judge_timeout,
            fail_fast=args.fail_fast,
            prompt_path=Path(args.judge_prompt),
            step_delay_seconds=args.step_delay,
        )
        results.append(result)
        if args.fail_fast and result["final_verdict"] in {"FAIL", "PARTIAL"}:
            break
        if args.scenario_delay > 0 and scenario is not scenarios[-1]:
            time.sleep(args.scenario_delay)

    summary = summarize_run(
        run_id=run_id,
        started_at=started_at,
        base_url=args.base_url,
        tenant_id=args.tenant_id,
        judge_enabled=args.judge,
        scenario_results=results,
    )
    write_json(output_dir / "raw_runs.json", {"run_id": run_id, "scenarios": results})
    write_json(output_dir / "summary.json", summary)
    (output_dir / "summary.md").write_text(render_summary_markdown(summary), encoding="utf-8")
    return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hybrid deterministic + optional LLM chatbot evaluations.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--surface", default="dashboard")
    parser.add_argument("--trace-prefix", default="hybrid-eval")
    parser.add_argument("--scenario-file", default=str(DEFAULT_SCENARIO_FILE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--max-runs", type=int, default=None)
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--judge-timeout", type=float, default=30)
    parser.add_argument("--judge-prompt", default=str(DEFAULT_JUDGE_PROMPT))
    parser.add_argument("--step-delay", type=float, default=0)
    parser.add_argument("--scenario-delay", type=float, default=1)
    parser.add_argument("--fail-fast", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_dir = Path(args.output_dir)
    run_count = 0
    while True:
        run_count += 1
        target_dir = output_dir
        if args.loop:
            target_dir = output_dir / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        summary = run_once(args, target_dir)
        print(
            f"run={summary['run_id']} pass={summary['pass_count']} "
            f"fail={summary['fail_count']} partial={summary['partial_count']} output={target_dir}"
        )
        if args.fail_fast and (summary["fail_count"] or summary["partial_count"]):
            return 1
        if not args.loop:
            return 1 if summary["fail_count"] else 0
        if args.max_runs is not None and run_count >= args.max_runs:
            return 0 if summary["fail_count"] == 0 else 1
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
