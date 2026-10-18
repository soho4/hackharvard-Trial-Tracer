"""Independent continuation challenge against real newly authored file bytes."""

import importlib.util
import json

import pytest

from conftest import ROOT


@pytest.fixture(scope="module")
def challenge():
    spec = importlib.util.spec_from_file_location("independent_g3", ROOT / "tools/run_independent_challenge_g3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unfamiliar_real_files_literal_calendar_and_join_oracle(challenge, tmp_path):
    records, expected = challenge.authored_dataset()
    paths = challenge.write_dataset(tmp_path / "actual-inputs", records)
    output = tmp_path / "actual-result.json"
    result = challenge.cli_run(paths, output)
    assert result.returncode == 0, result.stderr
    challenge.assert_report(json.loads(output.read_bytes()), paths, records, expected)


def test_changing_one_unfamiliar_actual_date_only_changes_its_arithmetic(challenge, tmp_path):
    records, expected = challenge.authored_dataset()
    paths = challenge.write_dataset(tmp_path / "inputs", records)
    output = tmp_path / "first.json"
    first = challenge.cli_run(paths, output)
    assert first.returncode == 0, first.stderr
    before = json.loads(output.read_bytes())
    records["visits.csv"][5]["actual_date"] = "2000-03-04"
    expected[5]["status"] = "POTENTIAL_DEVIATION"
    expected[5]["calculation"]["actual"] = "2000-03-04"
    expected[5]["calculation"]["days_outside"] = 1
    paths = challenge.write_dataset(tmp_path / "inputs", records)
    changed = challenge.cli_run(paths, output)
    assert changed.returncode == 0, changed.stderr
    after = json.loads(output.read_bytes())
    challenge.assert_report(after, paths, records, expected)
    assert before["run_id"] != after["run_id"]
    for ordinal, (old, new) in enumerate(zip(before["findings"], after["findings"])):
        if ordinal != 5:
            assert old["status"] == new["status"]
            assert old["calculation"] == new["calculation"]


@pytest.mark.parametrize("corruption", ["embedded_nul", "wrong_delimiter", "blank_record", "extra_cell", "truncated_quote", "invalid_utf8"])
def test_malformed_unfamiliar_upload_after_success_refuses_and_preserves_previous(challenge, tmp_path, corruption):
    records, _ = challenge.authored_dataset()
    paths = challenge.write_dataset(tmp_path / "inputs", records)
    output = tmp_path / "latest.json"
    first = challenge.cli_run(paths, output)
    assert first.returncode == 0, first.stderr
    accepted = output.read_bytes()
    path = paths["visits.csv"]
    raw = path.read_bytes()
    if corruption == "embedded_nul":
        raw = raw.replace(b"SAFETY_PHONE_CALL", b"SAFETY\x00PHONE_CALL", 1)
    elif corruption == "wrong_delimiter":
        raw = raw.replace(b",", b";")
    elif corruption == "blank_record":
        raw += b"\r\n"
    elif corruption == "extra_cell":
        first_newline = raw.index(b"\r\n", 3)
        second_newline = raw.index(b"\r\n", first_newline + 2)
        raw = raw[:second_newline] + b",extra" + raw[second_newline:]
    elif corruption == "truncated_quote":
        raw += b'"unterminated'
    else:
        raw += b"\xff"
    path.write_bytes(raw)
    result = challenge.cli_run(paths, output)
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert not output.exists()
    diagnostics = json.loads(output.with_suffix(output.suffix + ".diagnostics.json").read_bytes())
    assert diagnostics["success_bundle_written"] is False
    assert diagnostics["diagnostic"]["code"]
    assert any(candidate.read_bytes() == accepted for candidate in (tmp_path / ".previous").iterdir())
