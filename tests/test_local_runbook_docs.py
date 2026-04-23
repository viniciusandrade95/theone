from pathlib import Path


WORKSPACE_COMMANDS = [
    "./start_theone.sh",
    "./capture_runtime_auth.sh",
    "./start_chatbot1.sh",
    "./quick_chatbot_evidence.sh",
    "./run_sidequest_loop.sh",
    "./compare_sidequest_runs.py sidequest_local_OLD sidequest_local_NEW",
    "./stop_local_stack.sh",
]


def test_theone_local_docs_match_workspace_runbook_entrypoints() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = repo_root.parent

    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    local_dev = (repo_root / "docs" / "runbooks" / "local-dev.md").read_text(
        encoding="utf-8"
    )

    assert "/home/vinicius/system-audit/workspace/LOCAL_RUNBOOK.md" in readme
    assert "próximo foco" in local_dev.lower()

    for command in WORKSPACE_COMMANDS:
        assert command in local_dev

    for rel_path in [
        "LOCAL_RUNBOOK.md",
        "start_theone.sh",
        "capture_runtime_auth.sh",
        "start_chatbot1.sh",
        "quick_chatbot_evidence.sh",
        "run_sidequest_loop.sh",
        "compare_sidequest_runs.py",
        "stop_local_stack.sh",
    ]:
        assert (workspace_root / rel_path).exists(), rel_path
