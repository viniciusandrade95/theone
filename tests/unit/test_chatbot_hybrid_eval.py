import json
from argparse import Namespace
from datetime import datetime, timezone

from scripts import chatbot_hybrid_eval as eval_runner


def test_load_scenarios_accepts_core_file():
    scenarios = eval_runner.load_scenarios(eval_runner.DEFAULT_SCENARIO_FILE)

    names = {scenario["name"] for scenario in scenarios}

    assert "booking_happy_path_full" in names
    assert "booking_missing_name" in names
    assert len(scenarios) >= 10


def test_extract_step_summary_handles_nested_workflow_result():
    body = {
        "conversation_id": "c-1",
        "session_id": "s-1",
        "status": "ok",
        "reply": {"text": "Tudo certo"},
        "trace_id": "t-1",
        "meta": {
            "source": "chatbot1",
            "raw": {
                "route": "workflow",
                "workflow": "book_appointment",
                "workflow_result": {
                    "status": "awaiting_confirmation",
                    "slots": {"service": "Corte"},
                    "action_result": {"pending_confirmation": True},
                },
            },
        },
    }

    summary = eval_runner.extract_step_summary(body)

    assert summary.conversation_id == "c-1"
    assert summary.session_id == "s-1"
    assert summary.workflow == "book_appointment"
    assert summary.workflow_status == "awaiting_confirmation"
    assert summary.slots["service"] == "Corte"


def test_deterministic_assertions_fail_on_stub_and_missing_slot():
    http = eval_runner.HttpResult(
        status_code=200,
        body_text=json.dumps({"meta": {"raw": {"workflow_result": {"action_result": {"mode": "prebooking_stub"}}}}}),
        json_body={"status": "ok"},
        headers={},
    )
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="ok",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="book_appointment",
        workflow_status="collecting",
        slots={},
        action_result={"mode": "prebooking_stub"},
    )

    result = eval_runner.evaluate_step(
        {"expected_workflow": "book_appointment", "expected_slots_present": ["service"]},
        http,
        summary,
        allow_prebooking_stub=False,
    )

    assert result.status == "FAIL"
    assert any("prebooking_stub" in reason for reason in result.reasons)
    assert any("expected slot service" in reason for reason in result.reasons)


def test_deterministic_assertions_allow_any_reply_phrase_for_semantic_wording():
    http = eval_runner.HttpResult(
        status_code=200,
        body_text=json.dumps({"status": "ok"}),
        json_body={"status": "ok"},
        headers={},
    )
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="Resumo para confirmação: Corte amanhã às 16:17. Tudo certo?",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="book_appointment",
        workflow_status="awaiting_confirmation",
        slots={"service": "Corte", "date": "2026-04-19", "time": "16:17"},
        action_result={},
    )

    result = eval_runner.evaluate_step(
        {"expected_reply_contains_any": ["confirmar", "confirmação", "posso encaminhar"]},
        http,
        summary,
        allow_prebooking_stub=False,
    )

    assert result.status == "PASS"


def test_expected_collecting_step_with_empty_slots_is_not_treated_as_reset():
    http = eval_runner.HttpResult(
        status_code=200,
        body_text=json.dumps({"status": "ok"}),
        json_body={"status": "ok"},
        headers={},
    )
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="Qual serviço você gostaria de agendar?",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="book_appointment",
        workflow_status="collecting",
        slots={},
        action_result={},
    )

    result = eval_runner.evaluate_step(
        {"expected_status": "collecting", "expected_no_rag_reset": True},
        http,
        summary,
        allow_prebooking_stub=False,
    )

    assert result.status == "PASS"


def test_expected_awaiting_confirmation_allows_completed_after_explicit_confirmation():
    http = eval_runner.HttpResult(
        status_code=200,
        body_text=json.dumps({"status": "ok"}),
        json_body={"status": "ok"},
        headers={},
    )
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="Pré-agendamento registrado.",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="book_appointment",
        workflow_status="completed",
        slots={"service": "Corte", "date": "2026-04-20", "time": "16:00"},
        action_result={"ok": True},
    )

    result = eval_runner.evaluate_step(
        {"user_message": "ok", "expected_status": "awaiting_confirmation"},
        http,
        summary,
        allow_prebooking_stub=False,
    )

    assert result.status == "PASS"


def test_allow_rag_detour_keeps_interruption_step_from_false_failure():
    http = eval_runner.HttpResult(
        status_code=200,
        body_text=json.dumps({"status": "ok"}),
        json_body={"status": "ok"},
        headers={},
    )
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="O endereço é Rua Principal, 123.",
        trace_id="t-1",
        source="chatbot1",
        route="rag",
        workflow=None,
        workflow_status=None,
        slots={},
        action_result={},
    )

    result = eval_runner.evaluate_step(
        {
            "expected_no_rag_reset": True,
            "allow_rag_detour": True,
            "expected_workflow_not": ["handoff_to_human"],
        },
        http,
        summary,
        allow_prebooking_stub=False,
    )

    assert result.status == "PASS"


def test_forbidden_workflow_catches_unexpected_handoff():
    http = eval_runner.HttpResult(
        status_code=200,
        body_text=json.dumps({"status": "ok"}),
        json_body={"status": "ok"},
        headers={},
    )
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="Vou encaminhar para um atendente.",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="handoff_to_human",
        workflow_status="awaiting_confirmation",
        slots={},
        action_result={},
    )

    result = eval_runner.evaluate_step(
        {"expected_workflow_not": ["handoff_to_human"]},
        http,
        summary,
        allow_prebooking_stub=False,
    )

    assert result.status == "FAIL"
    assert any("workflow must not be handoff_to_human" in reason for reason in result.reasons)


def test_transcript_building_uses_user_and_assistant_turns():
    transcript = eval_runner.build_transcript(
        [
            {"request": {"message": "Quero marcar"}, "summary": {"reply_text": "Qual serviço?"}},
            {"request": {"message": "Corte"}, "summary": {"reply_text": "Qual horário?"}},
        ]
    )

    assert "Turn 1 user: Quero marcar" in transcript
    assert "Turn 2 assistant: Qual horário?" in transcript


def test_malformed_judge_output_is_reported(monkeypatch, tmp_path):
    class FakeSettings:
        @classmethod
        def from_env(cls):
            return cls()

    class FakeClient:
        def __init__(self, settings):
            self.settings = settings

        def complete(self, *args, **kwargs):
            return "not json"

    prompt = tmp_path / "judge_prompt.md"
    prompt.write_text("Return JSON", encoding="utf-8")
    monkeypatch.setattr(eval_runner, "load_existing_llm_client", lambda: (FakeClient, FakeSettings))

    result = eval_runner.run_judge(
        prompt_path=prompt,
        scenario={"name": "s1", "description": "desc"},
        transcript="user: hi\nassistant: hello",
        deterministic_result={"final_verdict": "PASS"},
        judge_model="gpt-oss:20b",
        judge_timeout=1,
    )

    assert result["status"] == "FAILED"
    assert "raw_output" in result


def test_judge_mode_accepts_mocked_structured_output(monkeypatch, tmp_path):
    class FakeSettings:
        @classmethod
        def from_env(cls):
            return cls()

    class FakeClient:
        def __init__(self, settings):
            self.settings = settings

        def complete(self, *args, **kwargs):
            return json.dumps(
                {
                    "naturalness_score": 4,
                    "coherence_score": 5,
                    "task_effectiveness_score": 4,
                    "recovery_score": 4,
                    "asks_correct_next_question": True,
                    "stayed_on_task": True,
                    "sounded_human_enough": True,
                    "major_issues": [],
                    "minor_issues": ["Could be shorter."],
                    "summary": "Good conversation.",
                }
            )

    prompt = tmp_path / "judge_prompt.md"
    prompt.write_text("Return JSON", encoding="utf-8")
    monkeypatch.setattr(eval_runner, "load_existing_llm_client", lambda: (FakeClient, FakeSettings))

    result = eval_runner.run_judge(
        prompt_path=prompt,
        scenario={"name": "s1", "description": "desc"},
        transcript="user: hi\nassistant: hello",
        deterministic_result={"final_verdict": "PASS"},
        judge_model="gpt-oss:20b",
        judge_timeout=1,
    )

    assert result["status"] == "PASS"
    assert result["result"]["coherence_score"] == 5


def test_summary_generation_counts_failures_and_judge_issues():
    summary = eval_runner.summarize_run(
        run_id="r1",
        started_at="2026-04-18T00:00:00+00:00",
        base_url="https://example.test",
        tenant_id="tenant",
        judge_enabled=True,
        scenario_results=[
            {
                "scenario_name": "pass",
                "final_verdict": "PASS",
                "failures": [],
                "judge": {
                    "result": {
                        "naturalness_score": 5,
                        "coherence_score": 4,
                        "task_effectiveness_score": 5,
                        "recovery_score": 4,
                        "major_issues": [],
                        "minor_issues": ["wordy"],
                    }
                },
            },
            {
                "scenario_name": "fail",
                "final_verdict": "FAIL",
                "failure_records": [
                    {
                        "category": "assertion_failure",
                        "message": "expected workflow book_appointment, got rag",
                    }
                ],
                "failures": ["step 1: assertion_failure: expected workflow book_appointment, got rag"],
                "judge": {"status": "DISABLED"},
            },
        ],
    )

    assert summary["pass_count"] == 1
    assert summary["fail_count"] == 1
    assert summary["common_failure_patterns"]["assertion_failure"][0]["pattern"] == "expected workflow book_appointment, got rag"
    assert summary["top_judge_issues"][0]["issue"] == "wordy"


def test_failure_taxonomy_classifies_conversation_state_reset():
    record = eval_runner.make_failure(
        "assertion_failure",
        "workflow appears to have reset to collecting with empty slots",
        step_index=1,
    )

    assert record["failure_family"] == "conversation.state_reset"
    assert record["failure_layer"] == "conversation"
    assert record["category"] == "assertion_failure"


def test_failure_taxonomy_classifies_config_error_as_execution_not_slot_bug():
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="Configuração incompleta",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="book_appointment",
        workflow_status="failed",
        slots={"service": "Corte"},
        action_result={"ok": False, "error_code": "config_missing_services_json", "operational_status": "validation_error"},
    )

    record = eval_runner.make_failure(
        "assertion_failure",
        "expected status awaiting_confirmation, got response=ok workflow=failed",
        summary=summary,
    )

    assert record["failure_family"] == "execution.service_mapping_missing"
    assert record["failure_layer"] == "execution"


def test_failure_taxonomy_classifies_crm_ambiguity_as_execution_stage():
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="Encontrei mais de um agendamento possível.",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="reschedule_appointment",
        workflow_status="awaiting_target_reference",
        slots={"new_date": "2026-04-24", "new_time": "16:00"},
        action_result={"ok": False, "error_code": "appointment_ambiguous", "operational_status": "validation_error"},
    )

    record = eval_runner.make_failure(
        "assertion_failure",
        "expected status awaiting_confirmation, got response=ok workflow=awaiting_target_reference",
        summary=summary,
    )

    assert record["failure_family"] == "execution.crm_ambiguous_expected"
    assert record["failure_layer"] == "execution"


def test_summary_keeps_legacy_patterns_and_adds_failure_families():
    summary = eval_runner.summarize_run(
        run_id="r1",
        started_at="2026-04-18T00:00:00+00:00",
        base_url="https://example.test",
        tenant_id="tenant",
        judge_enabled=False,
        scenario_results=[
            {
                "scenario_name": "fail",
                "final_verdict": "FAIL",
                "failure_records": [
                    eval_runner.make_failure("heuristic_failure", "Repeated time question", failure_type="loop_detected")
                ],
                "judge": {"status": "DISABLED"},
            }
        ],
    )

    assert summary["common_failure_patterns"]["heuristic_failure"][0]["pattern"] == "Repeated time question"
    assert summary["common_failure_families"]["conversation.time_flexible_mishandled"][0]["pattern"] == "Repeated time question"
    assert summary["failure_layer_counts"][0] == {"layer": "conversation", "count": 1}


def test_transient_upstream_502_retries_and_records_attempts(monkeypatch):
    transient_body = {
        "error": "VALIDATION_ERROR",
        "details": {"message": "Chatbot service request failed", "status": 502},
    }
    ok_body = {"status": "ok", "reply": {"text": "ok"}}
    responses = [
        eval_runner.HttpResult(status_code=400, body_text=json.dumps(transient_body), json_body=transient_body, headers={}),
        eval_runner.HttpResult(status_code=200, body_text=json.dumps(ok_body), json_body=ok_body, headers={}),
    ]
    sleeps = []

    def fake_post_json(*args, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(eval_runner, "post_json", fake_post_json)

    result = eval_runner.post_json_with_retries(
        "https://example.test",
        {"message": "hi"},
        {},
        retry_backoffs=(0.1, 0.2),
        sleeper=sleeps.append,
    )

    assert result.status_code == 200
    assert sleeps == [0.1]
    assert len(result.attempts) == 2
    assert result.attempts[0]["transient_upstream_failure"] is True


def test_crm_verification_does_not_match_stale_appointments(monkeypatch):
    body = {
        "items": [
            {
                "id": "old",
                "service_name": "Corte",
                "starts_at": "2026-04-18T16:17:00Z",
                "created_at": "2026-04-17T00:00:00Z",
            }
        ]
    }

    monkeypatch.setattr(
        eval_runner,
        "get_json",
        lambda *args, **kwargs: eval_runner.HttpResult(
            status_code=200,
            body_text=json.dumps(body),
            json_body=body,
            headers={},
        ),
    )

    result = eval_runner.verify_crm(
        "https://example.test",
        "tenant",
        "token",
        {
            "appointments": {
                "expect_created": True,
                "from_dt": "2026-04-18T00:00:00Z",
                "to_dt": "2026-04-19T00:00:00Z",
                "created_after": "2026-04-18T00:00:00Z",
                "match": {
                    "starts_at": "2026-04-18T16:17:00Z",
                    "service_name_contains": "Corte",
                },
            }
        },
    )

    assert result["status"] == "FAIL"
    assert result["matched"] == []


def test_crm_verification_marks_weak_match_partial(monkeypatch):
    body = {"items": [{"id": "old", "service_name": "Corte"}]}
    monkeypatch.setattr(
        eval_runner,
        "get_json",
        lambda *args, **kwargs: eval_runner.HttpResult(
            status_code=200,
            body_text=json.dumps(body),
            json_body=body,
            headers={},
        ),
    )

    result = eval_runner.verify_crm(
        "https://example.test",
        "tenant",
        "token",
        {
            "appointments": {
                "expect_created": True,
                "from_dt": "2026-04-18T00:00:00Z",
                "to_dt": "2026-04-19T00:00:00Z",
                "match": {"service_name_contains": "Corte"},
            }
        },
    )

    assert result["status"] == "PARTIAL"
    assert any("expected date/time" in reason for reason in result["reasons"])


def test_crm_verification_supports_relative_window_and_start_time(monkeypatch):
    body = {
        "items": [
            {
                "id": "new",
                "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
                "service_name": "Corte (audit)",
                "starts_at": "2026-04-20T16:17:00Z",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }

    monkeypatch.setattr(
        eval_runner,
        "get_json",
        lambda *args, **kwargs: eval_runner.HttpResult(
            status_code=200,
            body_text=json.dumps(body),
            json_body=body,
            headers={},
        ),
    )

    result = eval_runner.verify_crm(
        "https://example.test",
        "tenant",
        "token",
        {
            "appointments": {
                "expect_created": True,
                "from_dt": "relative:tomorrow_start_utc",
                "to_dt": "relative:day_after_tomorrow_start_utc",
                "recent_created_within_seconds": 900,
                "match": {
                    "start_time": "16:17",
                    "service_id": "944cc6ff-4283-444f-bcc9-8281c5a5a9f6",
                    "service_name_contains": "Corte",
                },
            }
        },
    )

    assert result["status"] == "PASS"
    assert result["matched"][0]["id"] == "new"


def test_crm_verification_accepts_dynamic_service_id_when_service_name_matches(monkeypatch):
    body = {
        "items": [
            {
                "id": "new",
                "service_id": "runtime-service-id",
                "service_name": "Corte",
                "starts_at": "2026-04-20T16:17:00Z",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }

    monkeypatch.setattr(
        eval_runner,
        "get_json",
        lambda *args, **kwargs: eval_runner.HttpResult(
            status_code=200,
            body_text=json.dumps(body),
            json_body=body,
            headers={},
        ),
    )

    result = eval_runner.verify_crm(
        "https://example.test",
        "tenant",
        "token",
        {
            "appointments": {
                "expect_created": True,
                "from_dt": "2026-04-20T00:00:00Z",
                "to_dt": "2026-04-21T00:00:00Z",
                "recent_created_within_seconds": 900,
                "match": {
                    "start_time": "16:17",
                    "service_id": "stale-static-service-id",
                    "service_name_contains": "Corte",
                },
            }
        },
    )

    assert result["status"] == "PASS"
    assert result["matched"][0]["id"] == "new"


def test_crm_verification_matches_local_start_time_from_utc_stored_appointment(monkeypatch):
    body = {
        "items": [
            {
                "id": "new",
                "service_id": "runtime-service-id",
                "service_name": "Corte",
                "starts_at": "2026-04-23T19:17:00",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }

    monkeypatch.setattr(
        eval_runner,
        "get_json",
        lambda *args, **kwargs: eval_runner.HttpResult(
            status_code=200,
            body_text=json.dumps(body),
            json_body=body,
            headers={},
        ),
    )

    result = eval_runner.verify_crm(
        "https://example.test",
        "tenant",
        "token",
        {
            "appointments": {
                "expect_created": True,
                "from_dt": "2026-04-23T00:00:00Z",
                "to_dt": "2026-04-24T00:00:00Z",
                "recent_created_within_seconds": 900,
                "match": {
                    "start_time": "16:17",
                    "service_id": "stale-static-service-id",
                    "service_name_contains": "Corte",
                },
            }
        },
    )

    assert result["status"] == "PASS"
    assert result["matched"][0]["id"] == "new"


def test_empty_collecting_slots_are_allowed_for_flexible_time_prompt():
    summary = eval_runner.StepSummary(
        conversation_id="c-1",
        session_id="s-1",
        status="ok",
        reply_text="Claro. Para eu sugerir horários, qual serviço você quer?",
        trace_id="t-1",
        source="chatbot1",
        route="workflow",
        workflow="book_appointment",
        workflow_status="collecting",
        slots={},
        action_result={"time_flexible": True, "time_resolution_mode": "flexible"},
    )

    result = eval_runner.evaluate_step(
        {"expected_no_rag_reset": True},
        eval_runner.HttpResult(status_code=200, body_text="{}", json_body={}, headers={}),
        summary,
        allow_prebooking_stub=False,
    )

    assert result.status == "PASS"


def test_summary_markdown_separates_failure_categories():
    summary = eval_runner.summarize_run(
        run_id="r2",
        started_at="2026-04-18T00:00:00+00:00",
        base_url="https://example.test",
        tenant_id="tenant",
        judge_enabled=False,
        scenario_results=[
            {
                "scenario_name": "infra",
                "final_verdict": "PARTIAL",
                "failure_records": [
                    {"category": "upstream_runtime_failure", "message": "Chatbot service request failed"}
                ],
                "judge": {"status": "DISABLED"},
            },
            {
                "scenario_name": "crm",
                "final_verdict": "PARTIAL",
                "failure_records": [
                    {"category": "crm_verification_failure", "message": "match is ambiguous"}
                ],
                "judge": {"status": "DISABLED"},
            },
        ],
    )

    markdown = eval_runner.render_summary_markdown(summary)

    assert "## Upstream / Runtime Failures" in markdown
    assert "Chatbot service request failed" in markdown
    assert "## CRM Verification Failures" in markdown
    assert "match is ambiguous" in markdown


def test_run_scenario_no_judge_writes_outputs(monkeypatch, tmp_path):
    responses = [
        {
            "conversation_id": "c-1",
            "session_id": "s-1",
            "status": "ok",
            "reply": {"text": "Posso confirmar?"},
            "trace_id": "trace-1",
            "meta": {
                "source": "chatbot1",
                "raw": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_result": {
                        "status": "awaiting_confirmation",
                        "slots": {"service": "Corte", "date": "2026-04-18", "time": "16:17"},
                    },
                },
            },
        },
        {
            "conversation_id": "c-1",
            "session_id": "s-1",
            "status": "ok",
            "reply": {"text": "Registrado"},
            "trace_id": "trace-2",
            "meta": {
                "source": "chatbot1",
                "raw": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_result": {
                        "status": "completed",
                        "slots": {"service": "Corte", "date": "2026-04-18", "time": "16:17"},
                        "action_result": {"ok": True},
                    },
                },
            },
        },
    ]

    def fake_post_json(url, payload, headers, timeout):
        body = responses.pop(0)
        return eval_runner.HttpResult(status_code=200, body_text=json.dumps(body), json_body=body, headers={})

    monkeypatch.setattr(eval_runner, "post_json", fake_post_json)
    monkeypatch.setattr(eval_runner, "verify_crm", lambda *args, **kwargs: {"status": "SKIPPED", "reasons": []})

    scenario = {
        "name": "mock_booking",
        "description": "mock",
        "steps": [
            {
                "user_message": "Quero corte amanhã 16h17",
                "expected_workflow": "book_appointment",
                "expected_status": "awaiting_confirmation",
                "expected_slots_present": ["service", "date", "time"],
            },
            {
                "user_message": "sim",
                "expected_workflow": "book_appointment",
                "expected_status": "completed",
                "expected_action_result_fields": {"ok": True},
            },
        ],
    }

    result = eval_runner.run_scenario(
        scenario=scenario,
        base_url="https://example.test",
        tenant_id="tenant",
        token="token",
        surface="dashboard",
        trace_prefix="test",
        run_id="run",
        output_dir=tmp_path,
        judge=False,
        judge_model=None,
        judge_timeout=1,
        fail_fast=False,
        prompt_path=eval_runner.DEFAULT_JUDGE_PROMPT,
        step_delay_seconds=0,
    )

    assert result["final_verdict"] == "PASS"
    assert result["steps"][0]["request"]["start_new"] is True
    assert result["steps"][1]["request"]["conversation_id"] == "c-1"
    assert result["steps"][1]["request"]["start_new"] is False
    assert (tmp_path / "scenario_results" / "mock_booking.json").exists()


def test_run_once_no_judge_generates_summary(monkeypatch, tmp_path):
    scenario_file = tmp_path / "scenarios.json"
    scenario_file.write_text(
        json.dumps({"scenarios": [{"name": "s1", "description": "desc", "steps": [{"user_message": "hi"}]}]}),
        encoding="utf-8",
    )

    def fake_run_scenario(**kwargs):
        return {
            "scenario_name": kwargs["scenario"]["name"],
            "final_verdict": "PASS",
            "failures": [],
            "judge": {"status": "DISABLED"},
        }

    monkeypatch.setattr(eval_runner, "run_scenario", fake_run_scenario)
    args = Namespace(
        scenario_file=str(scenario_file),
        base_url="https://example.test",
        tenant_id="tenant",
        token="token",
        surface="dashboard",
        trace_prefix="trace",
        judge=False,
        judge_model=None,
        judge_timeout=1,
        judge_prompt=str(eval_runner.DEFAULT_JUDGE_PROMPT),
        step_delay=0,
        scenario_delay=0,
        fail_fast=False,
    )

    summary = eval_runner.run_once(args, tmp_path / "out")

    assert summary["pass_count"] == 1
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "raw_runs.json").exists()
