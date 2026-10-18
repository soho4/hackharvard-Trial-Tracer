"""Literal independent cases for a source-preserving mapping adapter."""
import csv
import hashlib
import io
import json
import zipfile

import pytest

from conftest import ROOT
from trialtrace.errors import InputError
from trialtrace.preparation import inspect_spreadsheet, prepare_spreadsheet, evidence_package


@pytest.fixture
def export():
    path = ROOT / "examples/preparation"
    return ((path / "synthetic-wide.csv").read_bytes(), json.loads((path / "mapping.json").read_text()))


def prepare(export, rule, rule_sha256, **kwargs):
    raw, profile = export
    return prepare_spreadsheet(raw, "outside-export.csv", profile["columns"], profile["completed_value"], rule, rule_sha256, scope_confirmed=True, **kwargs)


def test_actual_new_file_expected_results_and_complete_original_chain(export, rule, rule_sha256):
    prepared = prepare(export, rule, rule_sha256)
    bundle, encoded, zipped = evidence_package(prepared, rule, rule_sha256)
    expected = json.loads((ROOT / "examples/preparation/expected.json").read_text())
    assert [f["status"] for f in bundle["findings"]] == expected["statuses"]
    assert bundle["summary"]["statuses"] == expected["counts"]
    assert bundle["findings"][1]["calculation"] == expected["second_calculation"]
    assert len(bundle["findings"]) == expected["records"]
    assert all(f["calculation"] is None for f in bundle["findings"][2:])
    assert bundle["findings"][0]["participant_id"] == "=SYNTH-PREP-01"
    with zipfile.ZipFile(io.BytesIO(zipped)) as archive:
        assert archive.read("source.csv") == export[0]
        assert archive.read("evidence.json") == encoded
        manifest = json.loads(archive.read("preparation.json"))
        assert manifest["source_sha256"] == hashlib.sha256(export[0]).hexdigest()
        assert manifest["report_sha256"] == hashlib.sha256(encoded).hexdigest()
        assert manifest["unmapped_columns"] == ["operator_note"]
        assert len(manifest["lineage"]) == 7
        for role, (_, raw) in prepared["uploads"].items():
            assert archive.read(role) == raw
            assert manifest["generated_files"][role]["sha256"] == hashlib.sha256(raw).hexdigest()
        assert manifest["lineage"][3]["source_completion_value"] == "entered"
        assert manifest["lineage"][3]["generated_completion_value"] == "UNCONFIRMED"
    assert evidence_package(prepare(export, rule, rule_sha256), rule, rule_sha256)[2] == zipped


def test_explicit_scope_mapping_and_completion_required(export, rule, rule_sha256):
    raw, profile = export
    with pytest.raises(InputError, match="Confirm synthetic"):
        prepare_spreadsheet(raw, "a.csv", profile["columns"], "done", rule, rule_sha256)
    for mapping in ({}, {**profile["columns"], "actual_date": "nonexistent"}):
        with pytest.raises(InputError) as error:
            prepare_spreadsheet(raw, "a.csv", mapping, "done", rule, rule_sha256, scope_confirmed=True)
        assert error.value.code == "COLUMN_MAPPING"
    with pytest.raises(InputError) as error:
        prepare_spreadsheet(raw, "a.csv", {**profile["columns"], "actual_date": "dose_actual"}, "done", rule, rule_sha256, scope_confirmed=True)
    assert error.value.code == "COLUMN_REUSED"
    for value in ("", "missing", " done"):
        with pytest.raises(InputError) as error:
            prepare_spreadsheet(raw, "a.csv", profile["columns"], value, rule, rule_sha256, scope_confirmed=True)
        assert error.value.code == "COMPLETION_MAPPING"


@pytest.mark.parametrize("raw,code", [(b"", "EMPTY_FILE"), (b"\xff", "INVALID_UTF8"), (b"x\n\0", "NUL_BYTE"),
    (b"a,a\n1,2", "INVALID_HEADER"), (b" a,b\n1,2", "INVALID_HEADER"), (b"a\n1,2", "ROW_WIDTH"),
    (b'a\nx"y', "CSV_QUOTING"), (b'a\r1', "CSV_NEWLINE"), (b"a\n"+b"x"*10001, "CELL_SIZE_LIMIT"),
    (b"a\n"+b"x\n"*501, "RECORD_LIMIT"), (b"x"*1000001, "INPUT_SIZE_LIMIT"),
    ((",".join(str(i) for i in range(65))+"\n").encode(), "INVALID_HEADER")])
def test_ambiguous_and_bounded_inputs_rejected(raw, code):
    with pytest.raises(InputError) as error:
        inspect_spreadsheet(raw)
    assert error.value.code == code


def test_bom_multiline_quoted_values_and_logical_ordinals():
    sheet = inspect_spreadsheet(b'\xef\xbb\xbfa,b\r\n"line1\r\nline2",001\r\n')
    assert sheet["bom"] is True
    assert sheet["records"] == [{"record_ordinal": 1, "raw_record": {"a": "line1\r\nline2", "b": "001"}, "raw_csv": '"line1\r\nline2",001\r\n'}]
    assert inspect_spreadsheet(b'a,b\n')["records"] == []


def test_unused_source_change_and_mapping_change_retire_identity(export, rule, rule_sha256):
    raw, profile = export
    original = prepare(export, rule, rule_sha256)
    altered = prepare((raw.replace(b'Synthetic boundary', b'Changed note'), profile), rule, rule_sha256)
    assert original["manifest"]["preparation_id"] != altered["manifest"]["preparation_id"]
    assert evidence_package(original, rule, rule_sha256)[0]["run_id"] != evidence_package(altered, rule, rule_sha256)[0]["run_id"]
    switched = {**profile, "columns": {**profile["columns"], "actual_date": "dose_actual", "anchor_date": "phone_actual"}}
    assert prepare((raw, switched), rule, rule_sha256)["manifest"]["preparation_id"] != original["manifest"]["preparation_id"]


def test_no_duplicate_collapse_no_date_coercion_no_whitespace_trimming(export, rule, rule_sha256):
    raw, profile = export
    changed = raw.replace(b'DOSE-02', b'DOSE-01').replace(b'2028-02-22', b'02/22/2028').replace(b'SYNTH-PREP-03', b' SYNTH-PREP-03')
    prepared = prepare((changed, profile), rule, rule_sha256)
    rows = list(csv.DictReader(io.StringIO(prepared["uploads"]["anchors.csv"][1].decode())))
    assert len(rows) == 7 and rows[0]["anchor_id"] == rows[1]["anchor_id"] == "DOSE-01"
    assert rows[0]["anchor_date"] == "02/22/2028"
    assert rows[2]["participant_id"] == " SYNTH-PREP-03"
    bundle = evidence_package(prepared, rule, rule_sha256)[0]
    assert bundle["summary"]["statuses"]["PASS"] == 0
    assert all(f["calculation"] is None for f in bundle["findings"])


def test_changed_date_changes_real_calculation(export, rule, rule_sha256):
    raw, profile = export
    bundle = evidence_package(prepare((raw.replace(b'2028-03-03', b'2028-03-05'), profile), rule, rule_sha256), rule, rule_sha256)[0]
    assert bundle["findings"][0]["status"] == "POTENTIAL_DEVIATION"
    assert bundle["findings"][0]["calculation"]["days_outside"] == 2
