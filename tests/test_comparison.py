"""Saved-report comparisons preserve uncertainty and distinguish provenance."""

from copy import deepcopy
import json

import pytest

from conftest import ROOT
from trialtrace.comparison import compare_reports, load_report, validate_report
from trialtrace.errors import InputError
from trialtrace.exporter import serialize_bundle


def test_load_real_report_and_utf8_bom(records, make_bundle):
    bundle = make_bundle(records)
    raw = serialize_bundle(bundle)
    assert load_report(raw) == bundle
    assert load_report(b"\xef\xbb\xbf" + raw) == bundle
    assert validate_report(bundle) is None


def test_report_exact_byte_limit_and_one_over(records, make_bundle):
    raw = serialize_bundle(make_bundle(records))
    padded = raw + b" " * (2000000 - len(raw))
    assert load_report(padded) == json.loads(raw)
    with pytest.raises(InputError) as error:
        load_report(padded + b" ")
    assert error.value.code == "REPORT_SIZE_LIMIT"


def test_nested_duplicate_key_is_rejected(records, make_bundle):
    raw = serialize_bundle(make_bundle(records))
    raw = raw.replace(b'"kind":"DEMO_ENGINE"', b'"kind":"DEMO_ENGINE","kind":"CONTRACT_FIXTURE"', 1)
    with pytest.raises(InputError) as error:
        load_report(raw)
    assert error.value.code == "REPORT_DUPLICATE_KEY"


def test_legacy_fixture_without_study_identity_is_not_joined_from_protocol_metadata():
    fixture = load_report((ROOT / "features/evidence_viewer/fixtures/mixed.json").read_bytes())
    result = compare_reports(fixture, fixture)
    assert result["summary"]["matched"] == 0
    assert result["summary"]["unmatched_before"] == len(fixture["findings"])
    assert result["summary"]["unmatched_after"] == len(fixture["findings"])
    assert result["summary"]["added"] == result["summary"]["removed"] == 0


def test_empty_reports_compare_without_inventing_findings(records, make_bundle):
    records["visits.csv"] = []
    bundle = make_bundle(records)
    comparison = compare_reports(bundle, bundle)
    assert all(value == 0 for value in comparison["summary"].values())
    assert comparison["matched"] == comparison["unmatched_before"] == comparison["unmatched_after"] == []


@pytest.mark.parametrize("raw", [b"", b"\xff", b"{}", b"[]", b'{"run_id":"one","run_id":"two"}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":"\\ud800"}', b"[" * 1100 + b"]" * 1100, b" " * 2000001])
def test_bad_json_encoding_structure_and_size_are_structured_errors(raw):
    with pytest.raises(InputError) as error:
        load_report(raw)
    assert error.value.code


@pytest.mark.parametrize("corruption", ["hash", "duplicate_finding", "date", "status", "accounting_list", "accounting_bad_table", "accounting_bad_issue", "summary_list", "summary_wrong_count"])
def test_invalid_report_semantics_and_optional_extras_fail_without_tracebacks(records, make_bundle, corruption):
    bundle = make_bundle(records)
    if corruption == "hash":
        bundle["findings"][0]["evidence"][0]["sha256"] = "f" * 64
    elif corruption == "duplicate_finding":
        bundle["findings"].append(deepcopy(bundle["findings"][0]))
    elif corruption == "date":
        bundle["findings"][0]["calculation"]["actual"] = "2033-02-29"
    elif corruption == "status":
        bundle["findings"][0]["status"] = "NOT_EVALUABLE"
    elif corruption == "accounting_list":
        bundle["input_accounting"] = []
    elif corruption == "accounting_bad_table":
        bundle["input_accounting"]["anchors.csv"] = []
    elif corruption == "accounting_bad_issue":
        bundle["input_accounting"]["anchors.csv"]["issues"] = [{"unexpected": "value"}]
    elif corruption == "summary_list":
        bundle["summary"] = []
    else:
        bundle["summary"]["visit_evaluations"] = 999
    with pytest.raises(InputError):
        load_report(json.dumps(bundle).encode())
    with pytest.raises(InputError):
        compare_reports(bundle, bundle)


def test_identical_reports_are_unchanged_and_comparison_does_not_mutate(records, make_bundle):
    bundle = make_bundle(records)
    snapshot = deepcopy(bundle)
    result = compare_reports(bundle, bundle)
    assert result["summary"] == {"matched": 1, "changed": 0, "provenance_only": 0, "unchanged": 1, "added": 0, "removed": 0, "unmatched_before": 0, "unmatched_after": 0}
    assert result["context_changes"] == []
    assert result["matched"][0]["changed_fields"] == []
    assert result["matched"][0]["identity"]["visit_id"] == "visit-new-817"
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    result["matched"][0]["identity"]["visit_id"] = "changed-output-only"
    assert bundle == snapshot


def test_one_changed_date_is_one_substantive_change_other_hash_change_is_provenance_only(records, make_bundle):
    records["visits.csv"].append(dict(records["visits.csv"][0], visit_id="another-new-visit"))
    before = make_bundle(records)
    records["visits.csv"][0]["actual_date"] = "2033-01-04"
    after = make_bundle(records)
    assert before["findings"][0]["finding_id"] != after["findings"][0]["finding_id"]
    result = compare_reports(before, after)
    assert result["summary"]["matched"] == 2
    assert result["summary"]["changed"] == 1
    assert result["summary"]["provenance_only"] == 1
    first, second = result["matched"]
    assert first["change_kind"] == "changed"
    assert set(first["changed_fields"]) >= {"status", "calculation", "raw_evidence", "evidence_provenance"}
    assert first["changes"]["calculation"]["before"]["days_outside"] == 0
    assert first["changes"]["calculation"]["after"]["days_outside"] == 1
    assert second["change_kind"] == "provenance_only"
    assert second["changed_fields"] == ["evidence_provenance"]


def test_row_reordering_matches_identity_not_ordinal(records, make_bundle):
    records["visits.csv"].append(dict(records["visits.csv"][0], visit_id="another-new-visit", actual_date="2033-01-04"))
    before = make_bundle(records)
    records["visits.csv"].reverse()
    after = make_bundle(records)
    result = compare_reports(before, after)
    assert result["summary"]["matched"] == 2
    assert result["summary"]["changed"] == 0
    assert result["summary"]["provenance_only"] == 2
    assert result["matched"][0]["before_record_ordinal"] == 1
    assert result["matched"][0]["after_record_ordinal"] == 2


def test_raw_note_and_reason_changes_are_visible_without_timing_change(records, make_bundle):
    before = make_bundle(records)
    records["assignments.csv"][0]["mapping_note"] = "Changed synthetic explanation. No approval."
    after = make_bundle(records)
    after["findings"][0]["reason"] = "Changed exported reason text."
    result = compare_reports(before, after)
    assert result["summary"]["changed"] == 1
    assert "raw_evidence" in result["matched"][0]["changed_fields"]
    assert "reason" in result["matched"][0]["changed_fields"]
    assert "calculation" not in result["matched"][0]["changed_fields"]


def test_resolved_relationship_query_matches_visit_without_calling_it_improvement(records, make_bundle):
    correct_person = records["anchors.csv"][0]["participant_id"]
    records["anchors.csv"][0]["participant_id"] = "other-synthetic-person"
    before = make_bundle(records)
    records["anchors.csv"][0]["participant_id"] = correct_person
    after = make_bundle(records)
    result = compare_reports(before, after)
    assert result["summary"]["matched"] == result["summary"]["changed"] == 1
    change = result["matched"][0]["changes"]
    assert change["status"] == {"before": "DATA_QUERY", "after": "PASS"}
    assert change["calculation"]["before"] is None
    assert change["calculation"]["after"]["days_outside"] == 0
    assert result["matched"][0]["change_kind"] == "changed"


def test_rule_source_mode_producer_differences_prominent_and_not_clinical(records, make_bundle):
    before = make_bundle(records)
    after = deepcopy(before)
    # Existing fixture/probe formats can omit run_mode. They remain admissible
    # inputs; this test does not create or approve a reviewed-engine report.
    after["producer"] = {"kind": "ARITHMETIC_PROBE", "version": "test-only"}
    after.pop("run_mode")
    after["ruleset"]["sha256"] = "a" * 64
    after["source"]["retrieval_status"] = "SOURCE_UNAVAILABLE"
    result = compare_reports(before, after)
    assert {change["field"] for change in result["context_changes"]} >= {"ruleset", "source", "run_mode", "producer"}
    assert result["summary"]["changed"] == 0
    assert result["clinical_validation"] is False
    assert result["limitations"]


def test_study_identity_can_be_recovered_from_own_visit_evidence(records, make_bundle):
    before = make_bundle(records)
    after = deepcopy(before)
    del after["findings"][0]["study_id"]
    result = compare_reports(before, after)
    assert result["summary"]["matched"] == 1
    assert result["matched"][0]["identity"]["study_id"] == "NCT04470427"


@pytest.mark.parametrize("field,value", [("visit_id", None), ("visit_id", ""), ("participant_id", " spaced "), ("study_id", None)])
def test_missing_or_malformed_identity_is_unmatched_without_arbitrary_pairing(records, make_bundle, field, value):
    before = make_bundle(records)
    after = deepcopy(before)
    for bundle in (before, after):
        finding = bundle["findings"][0]
        finding[field] = value
        for evidence in finding["evidence"]:
            if evidence["source_file"] == "visits.csv":
                evidence["raw_record"][field] = value
    result = compare_reports(before, after)
    assert result["matched"] == []
    assert result["summary"]["added"] == result["summary"]["removed"] == 0
    assert len(result["unmatched_before"]) == len(result["unmatched_after"]) == 1


def test_conflicting_top_level_and_evidence_identity_is_not_matched(records, make_bundle):
    before = make_bundle(records)
    after = deepcopy(before)
    after["findings"][0]["participant_id"] = "different-person"
    result = compare_reports(before, after)
    assert result["matched"] == []
    assert result["unmatched_after"][0]["reason"] == "CONFLICTING_IDENTITY"


def test_duplicate_stable_identity_on_either_side_prevents_all_pairing(records, make_bundle):
    before = make_bundle(records)
    records["visits.csv"].append(dict(records["visits.csv"][0]))
    after = make_bundle(records)
    result = compare_reports(before, after)
    assert result["matched"] == []
    assert len(result["ambiguous_groups"]) == 1
    assert len(result["unmatched_before"]) == 1
    assert len(result["unmatched_after"]) == 2
    assert all(item["reason"] == "DUPLICATE_IDENTITY" for item in result["unmatched_before"] + result["unmatched_after"])
    assert result["summary"]["added"] == result["summary"]["removed"] == 0


@pytest.mark.parametrize("field,value", [("participant_id", "different-synthetic-person"), ("site_id", "different-synthetic-site"), ("participant_id", "")])
@pytest.mark.parametrize("duplicate_side", ["before", "after", "both"])
def test_duplicate_canonical_visit_key_never_pairs_cross_owner_or_site_records(records, make_bundle, field, value, duplicate_side):
    single = make_bundle(records)
    records["visits.csv"].append(dict(records["visits.csv"][0], **{field: value}))
    duplicate = make_bundle(records)
    before = duplicate if duplicate_side in ("before", "both") else single
    after = duplicate if duplicate_side in ("after", "both") else single
    result = compare_reports(before, after)
    assert result["summary"]["matched"] == 0
    assert result["summary"]["added"] == result["summary"]["removed"] == 0
    assert len(result["unmatched_before"]) == len(before["findings"])
    assert len(result["unmatched_after"]) == len(after["findings"])
    assert all(item["reason"] == "DUPLICATE_IDENTITY" for item in result["unmatched_before"] + result["unmatched_after"])
    assert len(result["ambiguous_groups"]) == 1
    assert result["ambiguous_groups"][0]["visit_key"] == {"study_id": "NCT04470427", "visit_id": "visit-new-817"}


def test_unique_removed_and_added_records_are_counted_without_cross_pairing(records, make_bundle):
    before = make_bundle(records)
    records["visits.csv"][0]["visit_id"] = "entirely-new-record-id"
    after = make_bundle(records)
    result = compare_reports(before, after)
    assert result["matched"] == []
    assert result["summary"]["removed"] == result["summary"]["added"] == 1
    assert result["unmatched_before"][0]["reason"] == "ONLY_BEFORE"
    assert result["unmatched_after"][0]["reason"] == "ONLY_AFTER"


def test_direct_object_non_json_and_cycles_are_structured_errors(records, make_bundle):
    bundle = make_bundle(records)
    for value in (float("nan"), "\ud800", object()):
        bad = deepcopy(bundle)
        bad["extra"] = value
        with pytest.raises(InputError):
            compare_reports(bad, bundle)
    bad = deepcopy(bundle)
    bad["extra"] = bad
    with pytest.raises(InputError):
        compare_reports(bad, bundle)
