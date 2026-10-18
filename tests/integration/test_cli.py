"""Subprocess tests exercise actual files and runtime without mocks or stubs."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import ROOT


def run_cli(paths, output, *, draft=True, extra=(), rule=None, cwd=None):
    command = [sys.executable, "-m", "trialtrace.cli"]
    for flag, name in [("--anchors", "anchors.csv"), ("--visits", "visits.csv"), ("--assignments", "assignments.csv")]:
        command.extend([flag, str(paths[name])])
    command.extend(["--rule", str(rule or ROOT / "rules/candidate_rule.json"), "--output", str(output)])
    if draft:
        command.append("--draft-synthetic")
    command.extend(extra)
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.run(command, cwd=cwd or ROOT, env=env, capture_output=True, text=True, timeout=30)


def assert_failed_with_diagnostics(result, output):
    assert result.returncode != 0, result.stdout + result.stderr
    assert not output.exists(), "failed new input must not leave a success at the requested path"
    diagnostic_path = output.with_suffix(output.suffix + ".diagnostics.json")
    assert diagnostic_path.exists()
    diagnostics = json.loads(diagnostic_path.read_text())
    assert diagnostics
    assert "Traceback" not in result.stderr
    return diagnostics


def test_actual_new_cli_inputs_change_result_when_date_changes(records, write_inputs, tmp_path):
    paths = write_inputs(records)
    output = tmp_path / "computed.json"
    result = run_cli(paths, output)
    assert result.returncode == 0, result.stderr
    first_bytes = output.read_bytes()
    first = json.loads(first_bytes)
    finding = first["findings"][0]
    assert finding["visit_id"] == "visit-new-817"
    assert finding["status"] == "PASS"
    assert finding["calculation"] == {"target": "2032-12-31", "earliest": "2032-12-31", "latest": "2033-01-03", "actual": "2033-01-01", "days_outside": 0}
    repeated = run_cli(paths, output)
    assert repeated.returncode == 0, repeated.stderr
    assert output.read_bytes() == first_bytes
    records["visits.csv"][0]["actual_date"] = "2033-01-04"
    paths = write_inputs(records)
    changed = run_cli(paths, output)
    assert changed.returncode == 0, changed.stderr
    second = json.loads(output.read_bytes())
    assert second["findings"][0]["status"] == "POTENTIAL_DEVIATION"
    assert second["findings"][0]["calculation"]["days_outside"] == 1
    assert second["run_id"] != first["run_id"]
    assert second["findings"][0]["finding_id"] != first["findings"][0]["finding_id"]
    assert next(item["sha256"] for item in second["input_files"] if item["name"] == "visits.csv") == hashlib.sha256(paths["visits.csv"].read_bytes()).hexdigest()


def test_corrupt_replacement_removes_stale_target_and_keeps_previous_run(records, write_inputs, tmp_path):
    paths = write_inputs(records)
    output = tmp_path / "result.json"
    good = run_cli(paths, output)
    assert good.returncode == 0, good.stderr
    previous = output.read_bytes()
    paths["visits.csv"].write_bytes(b"bad,header\nwrong,data\n")
    result = run_cli(paths, output)
    assert_failed_with_diagnostics(result, output)
    # The old report must survive separately under a distinguishable name.
    preserved = [path for path in tmp_path.rglob("*") if path.is_file() and path != output and path.read_bytes() == previous]
    assert preserved, "previous successful report was destroyed instead of preserved separately"


def test_reviewed_default_fails_closed_without_auto_draft(records, write_inputs, tmp_path):
    paths = write_inputs(records)
    output = tmp_path / "reviewed.json"
    result = run_cli(paths, output, draft=False)
    assert_failed_with_diagnostics(result, output)


@pytest.mark.parametrize("kind", ["invalid_utf8", "missing_file", "malformed_rule", "invalid_rule", "oversize"])
def test_cli_structural_and_configuration_failure_is_diagnostic(records, write_inputs, tmp_path, kind):
    paths = write_inputs(records)
    rule = None
    if kind == "invalid_utf8":
        paths["visits.csv"].write_bytes(b"\xff")
    elif kind == "missing_file":
        paths["anchors.csv"].unlink()
    elif kind == "oversize":
        paths["assignments.csv"].write_bytes(b"x" * 1000001)
    else:
        rule = tmp_path / "bad-rule.json"
        if kind == "malformed_rule":
            rule.write_text("{not-json}")
        else:
            content = json.loads((ROOT / "rules/candidate_rule.json").read_bytes())
            content["upper_days"] = -1
            rule.write_text(json.dumps(content))
    output = tmp_path / "failed.json"
    assert_failed_with_diagnostics(run_cli(paths, output, rule=rule), output)


def test_unknown_flag_is_not_ignored(records, write_inputs, tmp_path):
    result = run_cli(write_inputs(records), tmp_path / "unknown.json", extra=("--invented-flag",))
    assert result.returncode != 0
    assert not (tmp_path / "unknown.json").exists()


@pytest.mark.parametrize("extra", [("--invented-flag",), ("--visits",)])
def test_malformed_cli_replacement_cannot_leave_previous_success_at_target(records, write_inputs, tmp_path, extra):
    paths = write_inputs(records)
    output = tmp_path / "replacement.json"
    good = run_cli(paths, output)
    assert good.returncode == 0, good.stderr
    previous = output.read_bytes()
    result = run_cli(paths, output, extra=extra)
    diagnostics = assert_failed_with_diagnostics(result, output)
    assert diagnostics["diagnostic"]["code"] == "CLI_ARGUMENTS"
    preserved = [path for path in tmp_path.rglob("*") if path.is_file() and path != output and path.read_bytes() == previous]
    assert preserved


@pytest.mark.parametrize("role", ["anchors.csv", "visits.csv", "assignments.csv", "rule"])
def test_output_input_collision_refuses_without_moving_or_mutating_input(records, write_inputs, tmp_path, role):
    paths = write_inputs(records)
    rule_path = tmp_path / "candidate-rule.json"
    rule_path.write_bytes((ROOT / "rules/candidate_rule.json").read_bytes())
    protected = dict(paths, rule=rule_path)
    before = {name: path.read_bytes() for name, path in protected.items()}
    result = run_cli(paths, protected[role], rule=rule_path)
    assert result.returncode != 0
    diagnostics = json.loads(result.stderr)
    assert diagnostics["diagnostic"]["code"] == "OUTPUT_INPUT_COLLISION"
    assert {name: path.read_bytes() for name, path in protected.items()} == before
    assert not (tmp_path / ".previous").exists()


def test_diagnostics_input_collision_cannot_replace_or_move_input(records, write_inputs, tmp_path):
    paths = write_inputs(records)
    output = tmp_path / "report.json"
    diagnostic_path = output.with_suffix(output.suffix + ".diagnostics.json")
    paths["visits.csv"].rename(diagnostic_path)
    paths["visits.csv"] = diagnostic_path
    before = {name: path.read_bytes() for name, path in paths.items()}
    result = run_cli(paths, output)
    assert result.returncode != 0
    assert json.loads(result.stderr)["diagnostic"]["code"] == "OUTPUT_INPUT_COLLISION"
    assert {name: path.read_bytes() for name, path in paths.items()} == before
    assert not output.exists()


def test_diagnostics_directory_refuses_before_publishing_success_and_preserves_old_run(records, write_inputs, tmp_path):
    paths = write_inputs(records)
    output = tmp_path / "diagnostics-directory.json"
    good = run_cli(paths, output)
    assert good.returncode == 0, good.stderr
    previous = output.read_bytes()
    diagnostic_path = output.with_suffix(output.suffix + ".diagnostics.json")
    diagnostic_path.mkdir()
    result = run_cli(paths, output)
    assert result.returncode != 0
    assert not output.exists(), "failed report publication must not leave a new success file"
    assert diagnostic_path.is_dir(), "a user directory must not be removed or replaced"
    diagnostics = json.loads(result.stderr)
    assert diagnostics["status"] == "FAILED"
    assert diagnostics["success_bundle_written"] is False
    assert diagnostics["diagnostic"]["code"]
    assert "Traceback" not in result.stderr
    preserved = [path for path in (tmp_path / ".previous").glob("*") if path.is_file() and path.read_bytes() == previous]
    assert preserved, "old valid output must be preserved separately"


@pytest.mark.parametrize("kind,expected", [("missing_anchor", "DATA_QUERY"), ("unresolved", "NOT_EVALUABLE"), ("overflow", "DATA_QUERY")])
def test_cli_row_uncertainty_is_a_successful_honest_report(records, write_inputs, tmp_path, kind, expected):
    if kind == "missing_anchor":
        records["anchors.csv"] = []
    elif kind == "unresolved":
        records["assignments.csv"][0]["mapping_status"] = "UNRESOLVED"
    else:
        records["anchors.csv"][0]["anchor_date"] = "9999-12-29"
    output = tmp_path / "query.json"
    result = run_cli(write_inputs(records), output)
    assert result.returncode == 0, result.stderr
    bundle = json.loads(output.read_bytes())
    assert len(bundle["findings"]) == 1
    assert bundle["findings"][0]["status"] == expected
    assert bundle["findings"][0]["calculation"] is None


def test_cli_works_from_new_directory_without_frozen_labels(records, write_inputs, tmp_path):
    # Run entirely new files under an empty working directory. No answer file is supplied.
    location = tmp_path / "fresh-working-directory"
    location.mkdir()
    paths = write_inputs(records, directory=location / "new-inputs")
    output = location / "answer.json"
    result = run_cli(paths, output, cwd=location)
    assert result.returncode == 0, result.stderr
    assert not (location / "expected.json").exists()
    assert json.loads(output.read_bytes())["findings"][0]["status"] == "PASS"


def test_cli_empty_visits_does_not_claim_patient_compliance(records, write_inputs, tmp_path):
    records["visits.csv"] = []
    output = tmp_path / "empty.json"
    result = run_cli(write_inputs(records), output)
    assert result.returncode == 0, result.stderr
    bundle = json.loads(output.read_bytes())
    assert bundle["findings"] == []
    assert bundle["input_accounting"]["visits.csv"]["record_count"] == 0


def test_cli_does_not_emit_a_bundle_that_exceeds_viewer_limit(records, write_inputs, tmp_path):
    # A valid sub-limit input references the same long row 200 times. Full evidence
    # expansion exceeds 2 MB; this must fail explicitly instead of dropping rows.
    records["assignments.csv"][0]["mapping_note"] = "x" * 10000
    records["visits.csv"] = [dict(records["visits.csv"][0], visit_id=f"synthetic-overflow-{index}") for index in range(200)]
    output = tmp_path / "too-large.json"
    result = run_cli(write_inputs(records), output)
    assert_failed_with_diagnostics(result, output)


def test_duplicate_heavy_relationship_expansion_fails_with_explicit_size_code(records, write_inputs, tmp_path):
    # Each table is well below its own byte/row limits; preserving every conflicting
    # candidate across many visits makes the full evidence exceed the viewer limit.
    assignment = dict(records["assignments.csv"][0], mapping_note="x" * 1000)
    records["assignments.csv"] = [dict(assignment) for _ in range(100)]
    records["visits.csv"] = [dict(records["visits.csv"][0], visit_id=f"duplicate-expansion-{index}") for index in range(100)]
    paths = write_inputs(records)
    assert all(path.stat().st_size < 1000000 for path in paths.values())
    output = tmp_path / "expanded-conflicts.json"
    diagnostics = assert_failed_with_diagnostics(run_cli(paths, output), output)
    assert diagnostics["diagnostic"]["code"] == "OUTPUT_SIZE_LIMIT"
    assert diagnostics["success_bundle_written"] is False


def test_extreme_cell_cli_reports_declared_size_limit(records, write_inputs, tmp_path):
    records["assignments.csv"][0]["mapping_note"] = "x" * 140000
    output = tmp_path / "extreme-cell.json"
    diagnostics = assert_failed_with_diagnostics(run_cli(write_inputs(records), output), output)
    assert diagnostics["diagnostic"]["code"] == "CELL_SIZE_LIMIT"
