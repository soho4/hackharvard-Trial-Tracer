from copy import deepcopy
import hashlib
import json

import jsonschema
import pytest

from conftest import HEADERS, ROOT
from trialtrace.errors import InputError
from trialtrace.exporter import build_bundle, serialize_bundle, validate_bundle
from trialtrace.importer import load_inputs


def test_computed_bundle_conforms_to_pinned_json_schema(records, make_bundle):
    bundle = make_bundle(records)
    schema = json.loads((ROOT / "contracts/evidence_bundle.schema.json").read_text())
    jsonschema.Draft202012Validator(schema).validate(bundle)
    assert bundle["schema_version"] == "trialtrace.evidence.v1"
    assert bundle["data_kind"] == "SYNTHETIC"
    assert bundle["clinical_validation"] is False
    assert bundle["producer"]["kind"] == "DEMO_ENGINE"
    assert bundle["producer"]["version"]
    assert len(bundle["producer"]["code_sha256"]) == 64
    assert all(character in "0123456789abcdef" for character in bundle["producer"]["code_sha256"])
    assert bundle["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"
    assert bundle["run_mode"] == "DRAFT_ENGINEERING"
    assert any("unreviewed" in text.lower() or "pending" in text.lower() for text in bundle["limitations"])
    assert bundle["source"]["pdf_sha256"] is None
    assert bundle["source"]["retrieval_status"].upper() not in {"VERIFIED", "SOURCE_VERIFIED", "RETRIEVED_VERIFIED"}


def test_evidence_binds_to_actual_file_hashes_rows_and_record_ordinals(records, write_inputs, rule, rule_sha256):
    paths = write_inputs(records)
    bundle = build_bundle(load_inputs(paths), rule, rule_sha256, mode="DRAFT_ENGINEERING")
    declared = {item["name"]: item["sha256"] for item in bundle["input_files"]}
    assert set(declared) == set(HEADERS)
    for name in HEADERS:
        assert declared[name] == hashlib.sha256(paths[name].read_bytes()).hexdigest()
    evidence = bundle["findings"][0]["evidence"]
    assert {item["source_file"] for item in evidence} == set(HEADERS)
    for item in evidence:
        assert item["sha256"] == declared[item["source_file"]]
        assert item["record_ordinal"] == 1
        assert item["raw_record"] == records[item["source_file"]][0]
    assert bundle["ruleset"]["sha256"] == rule_sha256
    assert bundle["ruleset"]["version"] == "A10_DRAFT_2"
    assert bundle["ruleset"]["id"] == rule["rule_id"]


def test_repeat_input_preserves_identity_order_and_full_serialized_content(records, write_inputs, rule, rule_sha256):
    tables = load_inputs(write_inputs(records))
    first = build_bundle(tables, rule, rule_sha256, mode="DRAFT_ENGINEERING")
    second = build_bundle(tables, rule, rule_sha256, mode="DRAFT_ENGINEERING")
    assert first == second
    assert serialize_bundle(first) == serialize_bundle(second)
    assert json.loads(serialize_bundle(first)) == first
    assert serialize_bundle(first) == (json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def test_new_file_bytes_equal_parsed_values_change_snapshot_and_finding_identity(records, write_inputs, rule, rule_sha256, tmp_path):
    first = build_bundle(load_inputs(write_inputs(records, directory=tmp_path / "lf")), rule, rule_sha256, mode="DRAFT_ENGINEERING")
    second = build_bundle(load_inputs(write_inputs(records, directory=tmp_path / "crlf", newline="\r\n")), rule, rule_sha256, mode="DRAFT_ENGINEERING")
    assert first["findings"][0]["calculation"] == second["findings"][0]["calculation"]
    assert first["run_id"] != second["run_id"]
    assert first["findings"][0]["finding_id"] != second["findings"][0]["finding_id"]


def test_rule_locator_byte_change_changes_provenance_and_identity(records, write_inputs, rule, rule_sha256):
    tables = load_inputs(write_inputs(records))
    first = build_bundle(tables, rule, rule_sha256, mode="DRAFT_ENGINEERING")
    # This is deliberately labeled synthetic test configuration, never an approval.
    changed = deepcopy(rule)
    changed["source_locator"]["printed_pages"] = [150]
    changed_bytes = json.dumps(changed, sort_keys=True).encode()
    changed_sha = hashlib.sha256(changed_bytes).hexdigest()
    second = build_bundle(tables, changed, changed_sha, mode="DRAFT_ENGINEERING")
    assert first["ruleset"]["sha256"] != second["ruleset"]["sha256"]
    assert second["ruleset"]["sha256"] == changed_sha
    assert first["source"]["locator"] != second["source"]["locator"]
    assert first["run_id"] != second["run_id"]
    assert first["findings"][0]["finding_id"] != second["findings"][0]["finding_id"]
    assert second["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"


def test_missing_and_duplicate_visit_ids_still_have_one_unique_finding_per_source_record(records, make_bundle):
    records["visits.csv"][0]["visit_id"] = ""
    records["visits.csv"].append(dict(records["visits.csv"][0]))
    bundle = make_bundle(records)
    assert len(bundle["findings"]) == 2
    assert len({finding["finding_id"] for finding in bundle["findings"]}) == 2
    assert [finding["record_ordinal"] for finding in bundle["findings"]] == [1, 2]
    assert all(finding["status"] == "DATA_QUERY" for finding in bundle["findings"])


@pytest.mark.parametrize("corruption", [
    "evidence_hash", "unknown_evidence_file", "missing_file_declaration", "duplicate_file_declaration",
    "duplicate_finding_id", "invalid_calendar", "bounds_reversed", "target_outside_bounds",
    "pass_positive_distance", "pass_date_outside", "flag_zero_distance", "flag_wrong_distance",
    "query_with_calculation", "not_evaluable_with_calculation", "pass_without_calculation",
    "boolean_distance", "negative_distance", "noninteger_distance", "clinical_validation",
])
def test_schema_and_semantic_corruption_is_rejected(records, make_bundle, corruption):
    bundle = make_bundle(records)
    finding = bundle["findings"][0]
    if corruption == "evidence_hash":
        finding["evidence"][0]["sha256"] = "0" * 64
    elif corruption == "unknown_evidence_file":
        finding["evidence"][0]["source_file"] = "not-declared.csv"
    elif corruption == "missing_file_declaration":
        bundle["input_files"] = [item for item in bundle["input_files"] if item["name"] != finding["evidence"][0]["source_file"]]
    elif corruption == "duplicate_file_declaration":
        bundle["input_files"].append(deepcopy(bundle["input_files"][0]))
    elif corruption == "duplicate_finding_id":
        bundle["findings"].append(deepcopy(finding))
    elif corruption == "invalid_calendar":
        finding["calculation"]["actual"] = "2033-02-29"
    elif corruption == "bounds_reversed":
        finding["calculation"]["earliest"] = "2033-01-04"
    elif corruption == "target_outside_bounds":
        finding["calculation"]["target"] = "2032-12-30"
    elif corruption == "pass_positive_distance":
        finding["calculation"]["days_outside"] = 1
    elif corruption == "pass_date_outside":
        finding["calculation"]["actual"] = "2033-01-04"
    elif corruption == "flag_zero_distance":
        finding["status"] = "POTENTIAL_DEVIATION"
    elif corruption == "flag_wrong_distance":
        finding["status"] = "POTENTIAL_DEVIATION"
        finding["calculation"]["actual"] = "2033-01-04"
        finding["calculation"]["days_outside"] = 2
    elif corruption == "query_with_calculation":
        finding["status"] = "DATA_QUERY"
    elif corruption == "not_evaluable_with_calculation":
        finding["status"] = "NOT_EVALUABLE"
    elif corruption == "pass_without_calculation":
        finding["calculation"] = None
    elif corruption == "boolean_distance":
        finding["calculation"]["days_outside"] = False
    elif corruption == "negative_distance":
        finding["calculation"]["days_outside"] = -1
    elif corruption == "noninteger_distance":
        finding["calculation"]["days_outside"] = 0.5
    elif corruption == "clinical_validation":
        bundle["clinical_validation"] = True
    with pytest.raises(InputError) as error:
        validate_bundle(bundle)
    assert error.value.code


def test_export_size_limit_is_bytes_and_never_truncates(records, make_bundle):
    bundle = make_bundle(records)
    bundle["additional_synthetic_note"] = "é" * 1000001
    before = deepcopy(bundle)
    with pytest.raises(InputError) as error:
        serialize_bundle(bundle)
    assert error.value.code
    assert bundle == before


def test_exact_output_byte_limit_is_accepted_then_one_more_refused(records, make_bundle):
    bundle = make_bundle(records)
    bundle["additional_synthetic_note"] = ""
    remaining = 2000000 - len(serialize_bundle(bundle))
    assert remaining > 0
    bundle["additional_synthetic_note"] = "x" * remaining
    assert len(serialize_bundle(bundle)) == 2000000
    bundle["additional_synthetic_note"] += "x"
    with pytest.raises(InputError):
        serialize_bundle(bundle)


def test_shifted_input_dates_update_evidence_hashes_without_changing_distance(records, make_bundle):
    records["visits.csv"][0]["actual_date"] = "2033-01-04"
    first = make_bundle(records)
    records["anchors.csv"][0]["anchor_date"] = "2033-01-24"
    records["visits.csv"][0]["actual_date"] = "2033-02-04"
    second = make_bundle(records)
    assert first["findings"][0]["status"] == second["findings"][0]["status"] == "POTENTIAL_DEVIATION"
    assert first["findings"][0]["calculation"]["days_outside"] == second["findings"][0]["calculation"]["days_outside"] == 1
    assert second["findings"][0]["calculation"]["earliest"] == "2033-01-31"
    assert second["findings"][0]["calculation"]["latest"] == "2033-02-03"
    first_hashes = {item["name"]: item["sha256"] for item in first["input_files"]}
    second_hashes = {item["name"]: item["sha256"] for item in second["input_files"]}
    assert first_hashes["anchors.csv"] != second_hashes["anchors.csv"]
    assert first_hashes["visits.csv"] != second_hashes["visits.csv"]
    assert first_hashes["assignments.csv"] == second_hashes["assignments.csv"]


def test_novel_runtime_cannot_read_the_expected_fixture_answers(records, write_inputs, rule, rule_sha256, monkeypatch):
    import builtins
    import io

    paths = write_inputs(records)
    original_open = builtins.open
    original_io_open = io.open

    def guard(opener):
        def guarded(file, *args, **kwargs):
            if not isinstance(file, int):
                assert "expected.json" not in str(file), "runtime attempted to read frozen expected answers"
                assert "core_draft" not in str(file), "runtime attempted to substitute bundled fixture data"
            return opener(file, *args, **kwargs)
        return guarded

    monkeypatch.setattr(builtins, "open", guard(original_open))
    monkeypatch.setattr(io, "open", guard(original_io_open))
    bundle = build_bundle(load_inputs(paths), rule, rule_sha256, mode="DRAFT_ENGINEERING")
    assert bundle["findings"][0]["visit_id"] == "visit-new-817"
    assert bundle["findings"][0]["status"] == "PASS"


def test_invalid_bundle_cannot_bypass_validation_during_serialization(records, make_bundle):
    bundle = make_bundle(records)
    bundle["findings"][0]["status"] = "CLEAN_PATIENT"
    with pytest.raises(InputError):
        serialize_bundle(bundle)


def test_bundle_api_requires_explicit_draft_opt_in(records, write_inputs, rule, rule_sha256):
    tables = load_inputs(write_inputs(records))
    with pytest.raises(InputError) as error:
        build_bundle(tables, rule, rule_sha256)
    assert error.value.code == "SOURCE_REVIEW_REQUIRED"


def test_consistent_but_noncanonical_evidence_role_is_rejected_for_demo_engine(records, make_bundle):
    bundle = make_bundle(records)
    assert bundle["producer"]["kind"] == "DEMO_ENGINE"
    for declaration in bundle["input_files"]:
        if declaration["name"] == "anchors.csv":
            declaration["name"] = "arbitrary-source.csv"
    for finding in bundle["findings"]:
        for item in finding["evidence"]:
            if item["source_file"] == "anchors.csv":
                item["source_file"] = "arbitrary-source.csv"
    # Internal hashes still agree. The stricter main-engine role contract must
    # reject inventing a fourth role or substituting an unknown logical table.
    with pytest.raises(InputError) as error:
        validate_bundle(bundle)
    assert error.value.code
