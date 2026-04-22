from __future__ import annotations

from argparse import Namespace

from scripts import chatbot_autonomous_tester as auto


def _args(tmp_path, **overrides):
    base = {
        "base_url": "https://example.test",
        "tenant_id": "tenant",
        "token": "token",
        "surface": "dashboard",
        "trace_prefix": "auto-test",
        "scenario_file": "docs/test_runs/scenarios/core_booking_scenarios.json",
        "output_dir": str(tmp_path),
        "mode": "generative",
        "max_iterations": 1,
        "deterministic_limit": None,
        "generated_count": 2,
        "generator_model": None,
        "generator_timeout": 1,
        "seed": 1,
        "judge": False,
        "judge_model": None,
        "judge_timeout": 1,
        "judge_prompt": "docs/test_runs/judge_prompt.md",
        "step_delay": 0,
        "scenario_delay": 0,
        "loop_delay": 1,
        "fail_fast": False,
    }
    base.update(overrides)
    return Namespace(**base)


def test_generate_scenarios_falls_back_to_seed_when_llm_unavailable(monkeypatch):
    monkeypatch.setattr(auto.hybrid, "load_existing_llm_client", lambda: (_ for _ in ()).throw(RuntimeError("no llm")))

    scenarios, meta = auto.generate_scenarios(
        count=3,
        iteration=7,
        generator_model=None,
        generator_timeout=1,
        seed=42,
    )

    assert meta["status"] == "FALLBACK"
    assert len(scenarios) == 3
    assert all(scenario["generated"] is True for scenario in scenarios)
    assert all(scenario["name"].startswith("generated_i0007_") for scenario in scenarios)
    assert all(len(scenario["steps"]) >= 2 for scenario in scenarios)


def test_normalized_generated_booking_steps_get_operational_expectations():
    scenarios = auto.normalize_generated_scenarios(
        [
            {
                "name": "messy booking",
                "tags": ["booking", "fragmented"],
                "steps": [{"user_message": "quero marcar"}, {"user_message": "quanto custa?"}, {"user_message": "16h"}],
            }
        ],
        count=1,
        iteration=2,
    )

    assert scenarios[0]["steps"][0]["expected_workflow"] == "book_appointment"
    assert scenarios[0]["steps"][0]["expected_workflow_not"] == ["handoff_to_human"]
    assert scenarios[0]["steps"][1]["allow_rag_detour"] is True
    assert scenarios[0]["steps"][2]["expected_no_rag_reset"] is True


def test_heuristics_detect_slot_loss_and_premature_summary():
    result = {
        "steps": [
            {
                "step_index": 1,
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "collecting",
                    "reply_text": "Qual horário?",
                    "slots": {"service": "Corte", "date": "2026-04-20"},
                    "action_result": {},
                },
            },
            {
                "step_index": 2,
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "awaiting_confirmation",
                    "reply_text": "Resumo para confirmação",
                    "slots": {"service": "Corte"},
                    "action_result": {},
                },
            },
        ]
    }

    findings = auto.heuristic_findings(result, {"steps": [{}, {}]})
    finding_types = {finding["type"] for finding in findings}

    assert "slot_loss" in finding_types
    assert "premature_summary" in finding_types


def test_heuristics_allow_explicit_rag_detour():
    result = {
        "steps": [
            {
                "step_index": 1,
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "collecting",
                    "reply_text": "Qual dia?",
                    "slots": {"service": "Corte"},
                    "action_result": {},
                },
            },
            {
                "step_index": 2,
                "summary": {
                    "route": "rag",
                    "workflow": None,
                    "workflow_status": None,
                    "reply_text": "O endereço é Rua Principal.",
                    "slots": {},
                    "action_result": {},
                },
            },
        ]
    }

    findings = auto.heuristic_findings(result, {"steps": [{}, {"allow_rag_detour": True}]})

    assert all(finding["type"] != "rag_during_operational_flow" for finding in findings)


def test_heuristics_do_not_fail_awaiting_confirmation_expected_after_explicit_confirmation_completed():
    result = {
        "steps": [
            {
                "step_index": 1,
                "request": {"message": "quero marcar corte amanhã"},
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "awaiting_confirmation",
                    "reply_text": "Resumo para confirmação",
                    "slots": {"service": "Corte", "date": "2026-04-20", "time": "16:00"},
                    "action_result": {},
                },
            },
            {
                "step_index": 2,
                "request": {"message": "ok"},
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "completed",
                    "reply_text": "Pré-agendamento registrado.",
                    "slots": {"service": "Corte", "date": "2026-04-20", "time": "16:00"},
                    "action_result": {"ok": True},
                },
            },
        ]
    }
    scenario = {"steps": [{"user_message": "quero marcar corte amanhã"}, {"user_message": "ok"}], "expected_final_status": "awaiting_confirmation"}

    findings = auto.heuristic_findings(result, scenario)

    assert all(finding["type"] != "failure_to_complete_task" for finding in findings)


def test_add_heuristic_findings_adds_failure_taxonomy():
    result = {
        "failure_records": [],
        "steps": [
            {
                "step_index": 1,
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "collecting",
                    "reply_text": "Que horário?",
                    "slots": {"service": "Corte", "date": "2026-04-20"},
                    "action_result": {},
                },
            },
            {
                "step_index": 2,
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "collecting",
                    "reply_text": "Qual horário?",
                    "slots": {"service": "Corte", "date": "2026-04-20"},
                    "action_result": {},
                },
            },
            {
                "step_index": 3,
                "summary": {
                    "route": "workflow",
                    "workflow": "book_appointment",
                    "workflow_status": "collecting",
                    "reply_text": "Que horário?",
                    "slots": {"service": "Corte", "date": "2026-04-20"},
                    "action_result": {},
                },
            },
        ],
    }

    auto.add_heuristic_findings(result, {"steps": [{}, {}, {}], "tags": ["booking", "missing_time"]})

    assert result["failure_records"]
    assert result["failure_records"][0]["failure_family"] == "conversation.time_flexible_mishandled"
    assert result["failure_records"][0]["failure_layer"] == "conversation"


def test_question_classifier_ignores_confirmation_summaries_with_dates():
    assert (
        auto.classify_question(
            "Resumo para confirmação: pré-agendamento de Corte no dia 23 de abr às 16:17. Tudo certo por aqui?"
        )
        is None
    )
    assert auto.classify_question("Continuo com Corte no dia 23 de abr. Para fechar isso, preciso so do horario.") == "time"
    assert auto.classify_question("Qual dia fica melhor?") == "date"


def test_rolling_summary_tracks_top_failures(tmp_path):
    summary = {
        "iteration": 1,
        "run_id": "r1",
        "completed_at": "2026-04-19T00:00:00+00:00",
        "mode": "hybrid",
        "pass_count": 1,
        "fail_count": 1,
        "partial_count": 0,
        "top_5_failure_patterns": [{"pattern": "booking: slot loss", "count": 2}],
        "top_failure_types": [{"type": "slot_loss", "count": 2}],
    }

    auto.update_rolling_summary(tmp_path, summary)

    rolling = auto.load_json_object(tmp_path / "rolling_summary.json")
    assert rolling["iteration_count"] == 1
    assert rolling["top_5_failure_patterns"][0]["pattern"] == "booking: slot loss"
    assert (tmp_path / "top_failures.md").exists()


def test_run_iteration_writes_generated_outputs(monkeypatch, tmp_path):
    fake_scenarios = [
        {
            "name": "generated_i0001_01_test",
            "description": "test",
            "tags": ["generated", "booking"],
            "steps": [{"user_message": "quero marcar"}, {"user_message": "sim"}],
            "generated": True,
        }
    ]
    fake_result = {
        "scenario_name": "generated_i0001_01_test",
        "scenario_run_id": "run-generated_i0001_01_test",
        "description": "test",
        "tags": ["generated", "booking"],
        "final_verdict": "FAIL",
        "failure_records": [{"category": "heuristic_failure", "type": "slot_loss", "message": "Slot loss detected"}],
        "failures": ["heuristic_failure: Slot loss detected"],
        "steps": [],
        "judge": {"status": "DISABLED"},
    }

    monkeypatch.setattr(auto, "generate_scenarios", lambda **kwargs: (fake_scenarios, {"status": "FALLBACK"}))
    monkeypatch.setattr(auto, "run_scenarios", lambda **kwargs: [fake_result])

    summary = auto.run_iteration(_args(tmp_path), iteration=1)

    assert summary["fail_count"] == 1
    assert summary["top_failure_types"][0]["type"] == "slot_loss"
    assert (tmp_path / "rolling_summary.json").exists()
    assert list((tmp_path / "iterations").glob("0001-*"))
