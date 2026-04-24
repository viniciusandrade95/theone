#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import chatbot_hybrid_eval as hybrid


DEFAULT_OUTPUT_DIR = Path("docs/test_runs/autonomous")
DEFAULT_GENERATED_COUNT = 5
DEFAULT_LOOP_DELAY_SECONDS = 30.0
DEFAULT_GENERATION_TIMEOUT_SECONDS = 45.0

OPERATIONAL_WORKFLOWS = {"book_appointment", "reschedule_appointment", "cancel_appointment"}
BOOKING_CONFIRMATION_TERMS = ("confirma", "confirmar", "tudo certo", "pré-agendamento", "pre-agendamento")

GENERATION_INSTRUCTIONS = """\
You generate adversarial but realistic Portuguese chatbot evaluation scenarios.
Return valid JSON only, with this shape:
{
  "scenarios": [
    {
      "name": "short_snake_case_name",
      "description": "what user is trying to do",
      "tags": ["booking", "fragmented", "ptbr"],
      "steps": [
        {"user_message": "realistic user message"},
        {"user_message": "next user message"}
      ],
      "expected_final_status": "completed|awaiting_confirmation|collecting|unknown"
    }
  ]
}

Generate multi-turn conversations that resemble imperfect real users. Include a mix of:
- booking
- remarcação/rescheduling
- cancellation
- fragmented inputs
- colloquial PT-BR
- interruptions and FAQ detours
- ambiguous phrasing
- typos and corrections

Do not include secrets, API URLs, or personal data beyond test placeholders like "Audit User" and "11999998888".
Prefer 3 to 6 turns per scenario.
"""


SEED_GENERATED_SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "seed_colloquial_fragmented_booking",
        "description": "Colloquial fragmented booking with time correction.",
        "tags": ["generated", "booking", "fragmented", "ptbr", "correction"],
        "steps": [
            {"user_message": "mano queria cortar amanhã"},
            {"user_message": "pode ser corte"},
            {"user_message": "16h? nao, 17h melhor"},
            {"user_message": "Audit User, 11999998888"},
            {"user_message": "sim"},
        ],
        "expected_final_status": "completed",
    },
    {
        "name": "seed_missing_time_booking",
        "description": "Booking request where the user does not know the exact time yet.",
        "tags": ["generated", "booking", "missing_time", "ambiguous"],
        "steps": [
            {"user_message": "quero marcar mas nao sei horario"},
            {"user_message": "corte amanhã"},
            {"user_message": "de tarde"},
            {"user_message": "Audit User, telefone 11999998888"},
            {"user_message": "ok"},
        ],
        "expected_final_status": "awaiting_confirmation",
    },
    {
        "name": "seed_reschedule_ambiguous",
        "description": "Ambiguous rescheduling request with a new time later.",
        "tags": ["generated", "reschedule", "ambiguous"],
        "steps": [
            {"user_message": "da pra mudar pra sexta?"},
            {"user_message": "meu corte"},
            {"user_message": "16h"},
            {"user_message": "pode"},
        ],
        "expected_final_status": "unknown",
    },
    {
        "name": "seed_cancellation_colloquial",
        "description": "Cancellation request with colloquial phrasing.",
        "tags": ["generated", "cancellation", "ptbr"],
        "steps": [
            {"user_message": "não posso ir amanhã"},
            {"user_message": "cancela meu corte pfv"},
            {"user_message": "sim"},
        ],
        "expected_final_status": "unknown",
    },
    {
        "name": "seed_booking_with_faq_interruption",
        "description": "Booking flow interrupted by price question, then resumed.",
        "tags": ["generated", "booking", "interruption", "faq"],
        "steps": [
            {"user_message": "quero marcar corte amanhã"},
            {"user_message": "opa, quanto custa?"},
            {"user_message": "beleza, 16h17 então"},
            {"user_message": "Audit User, 11999998888"},
            {"user_message": "sim, pode confirmar"},
        ],
        "expected_final_status": "completed",
    },
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def generate_scenarios(
    *,
    count: int,
    iteration: int,
    generator_model: str | None,
    generator_timeout: float,
    seed: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prompt_payload = {
        "requested_count": count,
        "iteration": iteration,
        "examples": [
            "mano queria cortar amanhã",
            "da pra mudar pra sexta?",
            "quero marcar mas nao sei horario",
            "16h? nao 17h melhor",
            "opa, quanto custa?",
            "e o endereco?",
        ],
    }
    try:
        llm_client_cls, settings_cls = hybrid.load_existing_llm_client()
        previous_timeout = os.environ.get("LLM_TIMEOUT_S")
        os.environ["LLM_TIMEOUT_S"] = str(generator_timeout)
        try:
            settings = settings_cls.from_env()
            client = llm_client_cls(settings)
            raw = client.complete(
                json.dumps(prompt_payload, ensure_ascii=False, indent=2),
                model=generator_model,
                instructions=GENERATION_INSTRUCTIONS,
                temperature=0.8,
                allow_missing_key_mock=False,
            )
        finally:
            if previous_timeout is None:
                os.environ.pop("LLM_TIMEOUT_S", None)
            else:
                os.environ["LLM_TIMEOUT_S"] = previous_timeout
        parsed = hybrid.extract_json_from_text(raw)
        if parsed is None:
            raise ValueError("generator output was not valid JSON")
        scenarios = normalize_generated_scenarios(parsed.get("scenarios"), count=count, iteration=iteration)
        if not scenarios:
            raise ValueError("generator returned no usable scenarios")
        return scenarios, {"status": "PASS", "source": "llm", "raw_output": raw}
    except Exception as exc:
        scenarios = fallback_generated_scenarios(count=count, iteration=iteration, seed=seed)
        return scenarios, {"status": "FALLBACK", "source": "seed", "error": str(exc)}


def fallback_generated_scenarios(*, count: int, iteration: int, seed: int | None = None) -> list[dict[str, Any]]:
    rng = random.Random(seed if seed is not None else iteration)
    pool = list(SEED_GENERATED_SCENARIOS)
    rng.shuffle(pool)
    selected = [pool[index % len(pool)] for index in range(max(0, count))]
    return normalize_generated_scenarios(selected, count=count, iteration=iteration)


def normalize_generated_scenarios(raw_scenarios: Any, *, count: int, iteration: int) -> list[dict[str, Any]]:
    if not isinstance(raw_scenarios, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_scenarios[:count], start=1):
        if not isinstance(raw, dict):
            continue
        raw_steps = raw.get("steps")
        if not isinstance(raw_steps, list) or len(raw_steps) < 2:
            continue
        tags = sorted({str(tag).strip().lower() for tag in raw.get("tags", []) if str(tag).strip()})
        if "generated" not in tags:
            tags.insert(0, "generated")
        name_base = hybrid.slugify(str(raw.get("name") or f"generated_{index}"))
        scenario_name = f"generated_i{iteration:04d}_{index:02d}_{name_base}"
        steps: list[dict[str, Any]] = []
        for step_index, raw_step in enumerate(raw_steps, start=1):
            if isinstance(raw_step, dict):
                message = str(raw_step.get("user_message") or "").strip()
                incoming = raw_step
            else:
                message = str(raw_step or "").strip()
                incoming = {}
            if not message:
                continue
            steps.append(default_generated_step(message=message, tags=tags, step_index=step_index, incoming=incoming))
        if len(steps) < 2:
            continue
        expected_final_status = str(raw.get("expected_final_status") or "unknown").strip().lower()
        normalized.append(
            {
                "name": scenario_name,
                "description": str(raw.get("description") or "LLM-generated autonomous scenario").strip(),
                "tags": tags,
                "steps": steps,
                "expected_final_status": expected_final_status,
                "generated": True,
                "generation_iteration": iteration,
            }
        )
    return normalized


def default_generated_step(*, message: str, tags: list[str], step_index: int, incoming: dict[str, Any]) -> dict[str, Any]:
    step = {
        "user_message": message,
        "expected_reply_not_contains": ["prebooking_stub", "erro técnico"],
    }
    lowered = message.casefold()
    is_interruption = any(term in lowered for term in ("quanto", "custa", "preço", "preco", "endereço", "endereco"))
    is_booking = "booking" in tags or any(term in lowered for term in ("marcar", "agendar", "corte", "horario", "horário"))
    is_reschedule = "reschedule" in tags or any(term in lowered for term in ("remarcar", "mudar", "trocar"))
    is_cancel = "cancellation" in tags or any(term in lowered for term in ("cancel", "desmarcar", "não posso", "nao posso"))
    if is_interruption and step_index > 1:
        step.update({"allow_rag_detour": True, "expected_workflow_not": ["handoff_to_human"], "expected_no_rag_reset": True})
        return merge_allowed_step_fields(step, incoming)
    if is_reschedule:
        step.update({"expected_workflow": "reschedule_appointment", "expected_no_rag_reset": True})
    elif is_cancel:
        step.update({"expected_workflow": "cancel_appointment", "expected_no_rag_reset": True})
    elif is_booking:
        step.update({"expected_workflow": "book_appointment", "expected_no_rag_reset": True})
    if is_booking or is_reschedule or is_cancel:
        step["expected_workflow_not"] = ["handoff_to_human"]
    return merge_allowed_step_fields(step, incoming)


def merge_allowed_step_fields(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "expected_route",
        "expected_workflow",
        "expected_status",
        "expected_reply_contains",
        "expected_reply_contains_any",
        "expected_reply_not_contains",
        "expected_slots_present",
        "expected_action_result_fields",
        "expected_no_rag_reset",
        "allow_rag_detour",
        "expected_workflow_not",
        "allow_empty_collecting_slots",
    }
    merged = dict(base)
    for key in allowed:
        if key in incoming:
            merged[key] = incoming[key]
    return merged


def run_scenarios(
    *,
    scenarios: list[dict[str, Any]],
    args: argparse.Namespace,
    run_id: str,
    output_dir: Path,
    group: str,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        result = hybrid.run_scenario(
            scenario=scenario,
            base_url=args.base_url,
            tenant_id=args.tenant_id,
            token=args.token,
            surface=args.surface,
            trace_prefix=f"{args.trace_prefix}-{group}",
            run_id=run_id,
            output_dir=output_dir,
            judge=args.judge,
            judge_model=args.judge_model,
            judge_timeout=args.judge_timeout,
            fail_fast=args.fail_fast,
            prompt_path=Path(args.judge_prompt),
            step_delay_seconds=args.step_delay,
        )
        add_heuristic_findings(result, scenario)
        hybrid.write_scenario_outputs(output_dir, str(result["scenario_name"]), result)
        results.append(result)
        if args.fail_fast and result["final_verdict"] in {"FAIL", "PARTIAL"}:
            break
        if args.scenario_delay > 0 and scenario is not scenarios[-1]:
            time.sleep(args.scenario_delay)
    return results


def add_heuristic_findings(result: dict[str, Any], scenario: dict[str, Any]) -> None:
    records = list(result.get("failure_records") or [])
    for finding in heuristic_findings(result, scenario):
        records.append(
            hybrid.make_failure(
                "heuristic_failure",
                finding["message"],
                step_index=finding.get("step_index"),
                failure_type=finding["type"],
                scenario=scenario,
            )
        )
    result["failure_records"] = records
    result["failures"] = [hybrid.failure_message(record) for record in records]
    result["heuristics"] = {
        "findings": [record for record in records if record.get("category") == "heuristic_failure"],
    }
    result["final_verdict"] = hybrid.final_verdict_from_failures(records)


def heuristic_findings(result: dict[str, Any], scenario: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    steps = result.get("steps") if isinstance(result.get("steps"), list) else []
    previous_slots: dict[str, Any] = {}
    repeated_questions = Counter()
    operational_seen = False
    for step in steps:
        step_index = int(step.get("step_index") or 0)
        summary = step.get("summary") if isinstance(step.get("summary"), dict) else {}
        workflow = summary.get("workflow")
        route = summary.get("route")
        status = summary.get("workflow_status") or summary.get("status")
        reply_text = str(summary.get("reply_text") or "")
        slots = summary.get("slots") if isinstance(summary.get("slots"), dict) else {}
        action = summary.get("action_result") if isinstance(summary.get("action_result"), dict) else {}
        if workflow in OPERATIONAL_WORKFLOWS:
            operational_seen = True
        if operational_seen and route == "rag" and not step_allows_rag_detour(scenario, step_index):
            findings.append({"type": "rag_during_operational_flow", "step_index": step_index, "message": "RAG route during operational flow"})
        if workflow == "handoff_to_human" and "handoff" not in scenario.get("tags", []):
            findings.append({"type": "unexpected_handoff", "step_index": step_index, "message": "Unexpected handoff during autonomous scenario"})
        lost = sorted(
            key for key, value in previous_slots.items() if value not in (None, "", [], {}) and slots.get(key) in (None, "", [], {})
        )
        if workflow in OPERATIONAL_WORKFLOWS and lost and status != "completed":
            findings.append({"type": "slot_loss", "step_index": step_index, "message": f"Slot loss detected: {', '.join(lost)}"})
        if workflow in OPERATIONAL_WORKFLOWS and slots:
            previous_slots.update({key: value for key, value in slots.items() if value not in (None, "", [], {})})
        question_kind = classify_question(reply_text)
        if question_kind:
            repeated_questions[question_kind] += 1
            if repeated_questions[question_kind] >= 3:
                findings.append({"type": "loop_detected", "step_index": step_index, "message": f"Repeated {question_kind} question"})
        if workflow == "book_appointment" and status == "awaiting_confirmation":
            missing = [slot for slot in ("service", "date", "time") if not slots.get(slot)]
            if missing:
                findings.append({"type": "premature_summary", "step_index": step_index, "message": f"Summary before required slots: {', '.join(missing)}"})
        if action.get("mode") == "prebooking_stub":
            findings.append({"type": "fake_success", "step_index": step_index, "message": "prebooking_stub used in autonomous run"})
    expected = str(scenario.get("expected_final_status") or "").lower()
    if expected in {"completed", "awaiting_confirmation", "collecting"}:
        final_status = str(hybrid.nested_get(steps[-1] if steps else {}, "summary.workflow_status", "") or "")
        if final_status != expected:
            if not (expected == "awaiting_confirmation" and final_status == "completed" and hybrid.scenario_ended_with_explicit_confirmation(scenario)):
                findings.append({"type": "failure_to_complete_task", "message": f"Expected final status {expected}, got {final_status or 'unknown'}"})
    if not steps:
        findings.append({"type": "dead_end", "message": "Scenario produced no step results"})
    return findings


def step_allows_rag_detour(scenario: dict[str, Any], step_index: int) -> bool:
    steps = scenario.get("steps")
    if not isinstance(steps, list) or step_index < 1 or step_index > len(steps):
        return False
    step = steps[step_index - 1]
    return isinstance(step, dict) and bool(step.get("allow_rag_detour"))


def classify_question(text: str) -> str | None:
    lowered = text.casefold()
    if "resumo para confirmação" in lowered or "resumo para confirmacao" in lowered:
        return None
    if "pré-agendamento" in lowered or "pre-agendamento" in lowered or "pre agendamento" in lowered:
        return None
    questionish = (
        "?" in lowered
        or "qual " in lowered
        or "que " in lowered
        or "prefere" in lowered
        or "preciso" in lowered
        or "informe" in lowered
    )
    if not questionish:
        return None
    if "serviço" in lowered or "servico" in lowered:
        return "service"
    if "qual dia" in lowered or "que dia" in lowered or "data" in lowered or "quando" in lowered:
        return "date"
    if "horário" in lowered or "horario" in lowered:
        return "time"
    if "nome" in lowered:
        return "customer_name"
    if "telefone" in lowered or "whats" in lowered or "zap" in lowered:
        return "phone"
    return None


def run_iteration(args: argparse.Namespace, *, iteration: int) -> dict[str, Any]:
    iteration_id = f"{utc_stamp()}-{uuid.uuid4().hex[:8]}"
    iteration_dir = Path(args.output_dir) / "iterations" / f"{iteration:04d}-{iteration_id}"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    started_at = hybrid.utc_now()
    all_results: list[dict[str, Any]] = []
    generated_scenarios: list[dict[str, Any]] = []
    generation_meta: dict[str, Any] = {"status": "SKIPPED"}

    if args.mode in {"deterministic", "hybrid"}:
        deterministic = hybrid.load_scenarios(Path(args.scenario_file))
        if args.deterministic_limit is not None:
            deterministic = deterministic[: args.deterministic_limit]
        all_results.extend(
            run_scenarios(
                scenarios=deterministic,
                args=args,
                run_id=iteration_id,
                output_dir=iteration_dir / "deterministic",
                group="deterministic",
            )
        )

    if args.mode in {"generative", "hybrid"}:
        generated_scenarios, generation_meta = generate_scenarios(
            count=args.generated_count,
            iteration=iteration,
            generator_model=args.generator_model,
            generator_timeout=args.generator_timeout,
            seed=args.seed,
        )
        write_json(iteration_dir / "generated_scenarios.json", {"scenarios": generated_scenarios, "generation": generation_meta})
        all_results.extend(
            run_scenarios(
                scenarios=generated_scenarios,
                args=args,
                run_id=iteration_id,
                output_dir=iteration_dir / "generated",
                group="generated",
            )
        )

    summary = build_autonomous_iteration_summary(
        iteration_id=iteration_id,
        iteration=iteration,
        started_at=started_at,
        args=args,
        results=all_results,
        generation_meta=generation_meta,
    )
    write_json(iteration_dir / "summary.json", summary)
    (iteration_dir / "summary.md").write_text(render_autonomous_summary_markdown(summary), encoding="utf-8")
    update_rolling_summary(Path(args.output_dir), summary)
    return summary


def build_autonomous_iteration_summary(
    *,
    iteration_id: str,
    iteration: int,
    started_at: str,
    args: argparse.Namespace,
    results: list[dict[str, Any]],
    generation_meta: dict[str, Any],
) -> dict[str, Any]:
    base_summary = hybrid.summarize_run(
        run_id=iteration_id,
        started_at=started_at,
        base_url=args.base_url,
        tenant_id=args.tenant_id,
        judge_enabled=args.judge,
        scenario_results=results,
    )
    failure_counter = Counter()
    pattern_counter = Counter()
    for result in results:
        scenario_tags = " ".join(str(tag) for tag in result.get("tags", []))
        for record in result.get("failure_records") or []:
            failure_type = str(record.get("failure_family") or record.get("type") or record.get("category") or "unknown")
            failure_counter[failure_type] += 1
            message = str(record.get("message") or "")
            if scenario_tags:
                pattern_counter[f"{scenario_tags}: {message[:120]}"] += 1
            else:
                pattern_counter[message[:160]] += 1
    base_summary.update(
        {
            "iteration": iteration,
            "mode": args.mode,
            "generation": generation_meta,
            "top_failure_types": [{"type": key, "count": count} for key, count in failure_counter.most_common(10)],
            "top_5_failure_patterns": [
                {"pattern": key, "count": count} for key, count in pattern_counter.most_common(5)
            ],
            "scenario_verdicts": [
                {
                    "scenario_name": result.get("scenario_name"),
                    "verdict": result.get("final_verdict"),
                    "tags": result.get("tags", []),
                    "failure_count": len(result.get("failure_records") or []),
                }
                for result in results
            ],
        }
    )
    return base_summary


def render_autonomous_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Chatbot Autonomous Tester Summary",
        "",
        f"- Iteration: {summary['iteration']}",
        f"- Run ID: {summary['run_id']}",
        f"- Mode: {summary['mode']}",
        f"- Started: {summary['started_at']}",
        f"- Completed: {summary['completed_at']}",
        f"- Total scenarios: {summary['total_scenarios']}",
        f"- Pass: {summary['pass_count']}",
        f"- Fail: {summary['fail_count']}",
        f"- Partial: {summary['partial_count']}",
        f"- Generation: {hybrid.nested_get(summary, 'generation.status', 'SKIPPED')}",
        "",
        "## Top 5 Failure Patterns",
        "",
    ]
    patterns = summary.get("top_5_failure_patterns") or []
    lines.extend([f"- {item['count']}x {item['pattern']}" for item in patterns] or ["- None"])
    lines.extend(["", "## Top Failure Types", ""])
    failure_types = summary.get("top_failure_types") or []
    lines.extend([f"- {item['count']}x {item['type']}" for item in failure_types] or ["- None"])
    lines.extend(["", "## Scenario Verdicts", ""])
    for item in summary.get("scenario_verdicts") or []:
        lines.append(f"- {item['verdict']}: {item['scenario_name']} ({item['failure_count']} findings)")
    return "\n".join(lines) + "\n"


def update_rolling_summary(output_dir: Path, iteration_summary: dict[str, Any]) -> None:
    path = output_dir / "rolling_summary.json"
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = load_json_object(path)
        except Exception:
            existing = {}
    iterations = list(existing.get("iterations") or [])
    compact = {
        "iteration": iteration_summary.get("iteration"),
        "run_id": iteration_summary.get("run_id"),
        "completed_at": iteration_summary.get("completed_at"),
        "mode": iteration_summary.get("mode"),
        "pass_count": iteration_summary.get("pass_count"),
        "fail_count": iteration_summary.get("fail_count"),
        "partial_count": iteration_summary.get("partial_count"),
        "top_5_failure_patterns": iteration_summary.get("top_5_failure_patterns", []),
        "top_failure_types": iteration_summary.get("top_failure_types", []),
    }
    iterations.append(compact)
    iterations = iterations[-100:]
    failure_patterns = Counter()
    failure_types = Counter()
    for item in iterations:
        for pattern in item.get("top_5_failure_patterns") or []:
            failure_patterns[str(pattern.get("pattern"))] += int(pattern.get("count") or 0)
        for failure_type in item.get("top_failure_types") or []:
            failure_types[str(failure_type.get("type"))] += int(failure_type.get("count") or 0)
    rolling = {
        "updated_at": hybrid.utc_now(),
        "iteration_count": len(iterations),
        "iterations": iterations,
        "top_5_failure_patterns": [
            {"pattern": key, "count": count} for key, count in failure_patterns.most_common(5)
        ],
        "most_frequent_bugs": [{"type": key, "count": count} for key, count in failure_types.most_common(10)],
    }
    write_json(path, rolling)
    (output_dir / "top_failures.md").write_text(render_rolling_failures_markdown(rolling), encoding="utf-8")


def render_rolling_failures_markdown(rolling: dict[str, Any]) -> str:
    lines = [
        "# Autonomous Chatbot Top Failures",
        "",
        f"- Updated: {rolling.get('updated_at')}",
        f"- Iterations tracked: {rolling.get('iteration_count')}",
        "",
        "## Top 5 Failure Patterns",
        "",
    ]
    patterns = rolling.get("top_5_failure_patterns") or []
    lines.extend([f"- {item['count']}x {item['pattern']}" for item in patterns] or ["- None"])
    lines.extend(["", "## Most Frequent Bugs", ""])
    bugs = rolling.get("most_frequent_bugs") or []
    lines.extend([f"- {item['count']}x {item['type']}" for item in bugs] or ["- None"])
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Continuously stress-test chatbot conversations with deterministic and generated scenarios.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--surface", default="dashboard")
    parser.add_argument("--trace-prefix", default="autonomous-eval")
    parser.add_argument("--scenario-file", default=str(hybrid.DEFAULT_SCENARIO_FILE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--mode", choices=["deterministic", "generative", "hybrid"], default="hybrid")
    parser.add_argument("--max-iterations", type=int, default=None)
    parser.add_argument("--deterministic-limit", type=int, default=None)
    parser.add_argument("--generated-count", type=int, default=DEFAULT_GENERATED_COUNT)
    parser.add_argument("--generator-model", default=None)
    parser.add_argument("--generator-timeout", type=float, default=DEFAULT_GENERATION_TIMEOUT_SECONDS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--judge-timeout", type=float, default=30)
    parser.add_argument("--judge-prompt", default=str(hybrid.DEFAULT_JUDGE_PROMPT))
    parser.add_argument("--step-delay", type=float, default=0.5)
    parser.add_argument("--scenario-delay", type=float, default=2.0)
    parser.add_argument("--loop-delay", type=float, default=DEFAULT_LOOP_DELAY_SECONDS)
    parser.add_argument("--fail-fast", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    iteration = 0
    while True:
        iteration += 1
        summary = run_iteration(args, iteration=iteration)
        print(
            f"iteration={iteration} run={summary['run_id']} mode={args.mode} "
            f"pass={summary['pass_count']} fail={summary['fail_count']} "
            f"partial={summary['partial_count']} output={args.output_dir}"
        )
        if args.fail_fast and (summary["fail_count"] or summary["partial_count"]):
            return 1
        if args.max_iterations is not None and iteration >= args.max_iterations:
            return 0 if summary["fail_count"] == 0 else 1
        time.sleep(max(float(args.loop_delay), 1.0))


if __name__ == "__main__":
    raise SystemExit(main())
