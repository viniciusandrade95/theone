import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "qa" / "error_catalog.json"


def test_error_catalog_entries_reference_existing_tests():
    assert CATALOG_PATH.exists(), "expected qa/error_catalog.json to exist"

    entries = json.loads(CATALOG_PATH.read_text())
    assert entries, "expected at least one regression entry"

    for entry in entries:
        assert entry["id"], "catalog entries must have an id"
        assert entry["title"], f"missing title for {entry}"
        assert entry["regression_tests"], f"missing regression_tests for {entry['id']}"

        for regression_test in entry["regression_tests"]:
            file_part = regression_test.split("::", 1)[0]
            file_path = ROOT / file_part
            assert file_path.exists(), f"catalog entry {entry['id']} references missing test file {file_part}"
