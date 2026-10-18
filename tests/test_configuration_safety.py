"""Configuration and option parsing must fail closed with preserved input files."""

import json
import os
import subprocess
import sys

import pytest

from conftest import ROOT
from trialtrace.errors import InputError
from trialtrace.exporter import build_bundle
from trialtrace.importer import load_inputs


def command_for(paths, output, rule_path):
    command = [sys.executable, "-m", "trialtrace.cli"]
    for role in ("anchors", "visits", "assignments"):
        command.extend(["--" + role, str(paths[role + ".csv"])])
    return command + ["--rule", str(rule_path), "--draft-synthetic", "--output", str(output)]


def run(command):
    return subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), capture_output=True, text=True, timeout=15)


def test_unpaired_surrogate_rule_is_a_structured_api_error(records, write_inputs, rule, rule_sha256):
    rule["interpretation_notes"] = ["Synthetic malformed note: \ud800"]
    with pytest.raises(InputError) as error:
        build_bundle(load_inputs(write_inputs(records)), rule, rule_sha256, mode="DRAFT_ENGINEERING")
    assert error.value.code


def test_escaped_unpaired_surrogate_rule_cli_has_diagnostics_without_traceback(records, write_inputs, rule, tmp_path):
    paths = write_inputs(records)
    rule["interpretation_notes"] = ["Synthetic malformed note: \ud800"]
    rule_path = tmp_path / "malformed-unicode-rule.json"
    rule_path.write_text(json.dumps(rule, ensure_ascii=True), encoding="utf-8")
    assert b"\\ud800" in rule_path.read_bytes()
    output = tmp_path / "malformed-unicode.json"
    result = run(command_for(paths, output, rule_path))
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert not output.exists()
    failure = json.loads(result.stderr)
    assert failure["status"] == "FAILED"
    assert failure["success_bundle_written"] is False
    assert failure["diagnostic"]["code"]
    saved = json.loads(output.with_suffix(output.suffix + ".diagnostics.json").read_text())
    assert saved == failure


@pytest.mark.parametrize("complete,abbreviated", [("--output", "--out"), ("--anchors", "--anch")])
def test_abbreviated_cli_options_are_rejected(records, write_inputs, tmp_path, complete, abbreviated):
    paths = write_inputs(records)
    output = tmp_path / "abbreviated.json"
    command = command_for(paths, output, ROOT / "rules/candidate_rule.json")
    command[command.index(complete)] = abbreviated
    result = run(command)
    assert result.returncode != 0, "abbreviations must not bypass the exact-option preflight"
    assert "Traceback" not in result.stderr
    assert json.loads(result.stderr)["diagnostic"]["code"] == "CLI_ARGUMENTS"
    assert not output.exists()


def test_abbreviated_output_cannot_overwrite_an_input(records, write_inputs):
    paths = write_inputs(records)
    before = {name: path.read_bytes() for name, path in paths.items()}
    command = command_for(paths, paths["visits.csv"], ROOT / "rules/candidate_rule.json")
    command[command.index("--output")] = "--out"
    result = run(command)
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert {name: path.read_bytes() for name, path in paths.items()} == before


def test_output_hardlink_to_anchor_input_is_rejected_without_moving_input(records, write_inputs, tmp_path):
    paths = write_inputs(records)
    before = {name: path.read_bytes() for name, path in paths.items()}
    output = tmp_path / "hardlinked-report.json"
    output.hardlink_to(paths["anchors.csv"])
    result = run(command_for(paths, output, ROOT / "rules/candidate_rule.json"))
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert json.loads(result.stderr)["diagnostic"]["code"] == "OUTPUT_INPUT_COLLISION"
    assert {name: path.read_bytes() for name, path in paths.items()} == before
    assert output.samefile(paths["anchors.csv"])
    assert output.read_bytes() == before["anchors.csv"]
    assert not (tmp_path / ".previous").exists()


def test_diagnostics_hardlink_to_visit_input_is_rejected_without_overwriting_input(records, write_inputs, tmp_path):
    paths = write_inputs(records)
    before = {name: path.read_bytes() for name, path in paths.items()}
    output = tmp_path / "diagnostic-hardlink-report.json"
    diagnostics_path = output.with_suffix(output.suffix + ".diagnostics.json")
    diagnostics_path.hardlink_to(paths["visits.csv"])
    result = run(command_for(paths, output, ROOT / "rules/candidate_rule.json"))
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert json.loads(result.stderr)["diagnostic"]["code"] == "OUTPUT_INPUT_COLLISION"
    assert {name: path.read_bytes() for name, path in paths.items()} == before
    assert diagnostics_path.samefile(paths["visits.csv"])
    assert diagnostics_path.read_bytes() == before["visits.csv"]
    assert not output.exists()
