"""Real parsed inputs and actual engine outputs exercise intake and review exports."""

import copy
import csv
import hashlib
import io
import json

import pytest

from trialtrace.errors import InputError
from trialtrace.importer import HEADERS, MAX_BYTES
from trialtrace.inspection import (
    build_input_issue_list, build_worklist, input_issues_csv, inspect_uploads,
    validate_input_accounting, worklist_csv,
)


def uploads(paths):
    return {role: ("locally authored " + role, path.read_bytes()) for role, path in paths.items()}


def csv_rows(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"), newline="")))


def test_partial_and_three_independent_parse_failures(rule, rule_sha256):
    missing = inspect_uploads({"visits.csv": None}, rule, rule_sha256)
    assert missing["missing_roles"] == list(HEADERS)
    assert not missing["ready_for_draft_check"]
    broken = {"anchors.csv": ("a.csv", b"\xff"), "visits.csv": ("v.csv", b"wrong,header\n"),
              "assignments.csv": ("s.csv", b'"unclosed')}
    result = inspect_uploads(broken, rule, rule_sha256)
    assert [item["problems"][0]["code"] for item in result["files"]] == ["INVALID_UTF8", "INVALID_HEADER", "CSV_QUOTING"]
    assert all(item["sha256"] == hashlib.sha256(broken[item["role"]][1]).hexdigest() for item in result["files"])
    assert result["relationship_summary"] is None and result["input_accounting"] is None
    assert not result["ready_for_draft_check"] and result["timing_evaluated"] is False


def test_intake_preserves_exact_bytes_bom_reordered_headers_and_multiline(records, write_inputs, rule, rule_sha256):
    records["assignments.csv"][0]["mapping_note"] = 'New source note, with "quoted" detail\r\nand next line.'
    paths = write_inputs(records, headers={name: list(reversed(fields)) for name, fields in HEADERS.items()}, newline="\r\n", bom=True)
    supplied = uploads(paths)
    original = copy.deepcopy(supplied)
    result = inspect_uploads(supplied, rule, rule_sha256)
    assert result["ready_for_draft_check"] and supplied == original
    assert result["relationship_summary"]["visit_records"] == 1
    assert result["relationship_summary"]["visits_with_issues"] == 0
    assert result["timing_evaluated"] is False
    for item in result["files"]:
        raw = supplied[item["role"]][1]
        assert (item["byte_count"], item["sha256"], item["bom"], item["record_count"]) == (len(raw), hashlib.sha256(raw).hexdigest(), True, 1)


def test_preflight_does_not_run_timing_or_infer_success(records, write_inputs, rule, rule_sha256, make_bundle):
    records["anchors.csv"][0]["anchor_date"] = "9999-12-31"
    result = inspect_uploads(uploads(write_inputs(records)), rule, rule_sha256)
    assert result["ready_for_draft_check"] and result["relationship_summary"]["visits_with_issues"] == 0
    assert "calculation" not in result["relationship_summary"]["visits"][0]
    assert make_bundle(records)["findings"][0]["reason_codes"] == ["DERIVED_DATE_OVERFLOW"]
    empty = inspect_uploads(uploads(write_inputs({role: [] for role in HEADERS})), rule, rule_sha256)
    assert empty["ready_for_draft_check"] and empty["relationship_summary"]["visit_records"] == 0
    assert empty["timing_evaluated"] is False


def test_structurally_valid_relationship_and_orphan_problems_stay_reviewable(records, write_inputs, rule, rule_sha256):
    records["anchors.csv"][0]["participant_id"] = "different-person"
    records["anchors.csv"].append(dict(records["anchors.csv"][0], anchor_id="unused-invalid", anchor_date="2032-02-30", anchor_kind="CONSENT"))
    records["visits.csv"][0]["assignment_id"] = "missing-mapping"
    result = inspect_uploads(uploads(write_inputs(records)), rule, rule_sha256)
    assert result["ready_for_draft_check"]
    assert result["relationship_summary"]["issue_occurrences_by_code"] == {"MISMATCH_PARTICIPANT_ID": 1, "MISSING_ASSIGNMENT_ID": 1}
    table = result["input_accounting"]["anchors.csv"]
    assert table["unreferenced_record_ordinals"] == [2]
    assert [(issue["record_ordinal"], issue["code"]) for issue in table["issues"]] == [(2, "UNSUPPORTED_ANCHOR_KIND"), (2, "INVALID_DATE")]


def test_configuration_and_unknown_role_block_readiness_but_files_are_inspected(records, write_inputs, rule, rule_sha256):
    rule["offset_days"] = True
    supplied = uploads(write_inputs(records)) | {"extra.csv": ("extra.csv", b"anything")}
    result = inspect_uploads(supplied, rule, "not-a-digest")
    assert [issue["code"] for issue in result["configuration_problems"]] == ["RULE_INTEGER", "RULE_HASH"]
    assert result["unexpected_roles"] == ["extra.csv"]
    assert all(item["state"] == "PARSED" for item in result["files"])
    assert not result["ready_for_draft_check"]


@pytest.mark.parametrize("upload,code", [("abc", "UPLOAD_SHAPE"), ((None, b"abc"), "UPLOAD_FILENAME"), (("name", "text"), "UPLOAD_BYTES"), (("name", bytearray(b"abc")), "UPLOAD_BYTES"), (("name", b"a" * (MAX_BYTES + 1)), "INPUT_SIZE_LIMIT")])
def test_no_upload_coercion(upload, code, rule, rule_sha256):
    result = inspect_uploads({"anchors.csv": upload}, rule, rule_sha256)
    assert result["files"][0]["problems"][0]["code"] == code
    assert not result["ready_for_draft_check"]


def test_bounded_evidence_amplification_rejects_without_truncating(records, write_inputs, rule, rule_sha256):
    records["anchors.csv"] = [dict(records["anchors.csv"][0], participant_id="p" * 1000) for _ in range(50)]
    records["visits.csv"] = [dict(records["visits.csv"][0], visit_id=f"novel-visit-{i}") for i in range(40)]
    result = inspect_uploads(uploads(write_inputs(records)), rule, rule_sha256)
    assert all(item["state"] == "PARSED" for item in result["files"])
    assert result["inspection_problems"][0]["code"] == "OUTPUT_SIZE_LIMIT"
    assert result["input_accounting"] is None and result["relationship_summary"] is None
    assert not result["ready_for_draft_check"]


def test_worklist_uses_real_findings_actions_and_provenance(records, make_bundle):
    base = records["visits.csv"][0]
    records["visits.csv"] = [dict(base), dict(base, visit_id="outside", actual_date="2033-01-04"),
                            dict(base, visit_id="missing", anchor_id="absent"), dict(base, visit_id="wrong-event", event_kind="BOOKING")]
    bundle = make_bundle(records)
    original = json.dumps(bundle, sort_keys=True)
    rows = build_worklist(bundle)
    assert [row["status"] for row in rows] == ["POTENTIAL_DEVIATION", "DATA_QUERY", "NOT_EVALUABLE"]
    assert len(build_worklist(bundle, include_pass=True)) == 4
    assert "unconfirmed" in rows[0]["suggested_action"]
    assert "absent reference does not prove a missed event" in rows[1]["suggested_action"]
    for row, finding in zip(rows, bundle["findings"][1:]):
        assert row["finding_id"] == finding["finding_id"]
        assert row["reason_codes"] == finding["reason_codes"]
        assert row["reason"] == finding["reason"]
        assert row["evidence_refs"] == [{key: item[key] for key in ("source_file", "record_ordinal", "sha256")} for item in finding["evidence"]]
        assert row["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"
    assert json.dumps(bundle, sort_keys=True) == original
    assert worklist_csv(bundle) == worklist_csv(bundle)


def test_accounting_export_keeps_each_issue_and_only_invalid_unused_rows(records, make_bundle):
    anchor = records["anchors.csv"][0]
    records["anchors.csv"] += [dict(anchor, anchor_id="valid-unused"), dict(anchor, anchor_id="bad-unused", anchor_date="2032-02-30", anchor_kind="BOOKING")]
    bundle = make_bundle(records)
    assert build_worklist(bundle) == []
    rows = build_input_issue_list(bundle)
    assert len(rows) == 2
    assert {row["code"] for row in rows} == {"INVALID_DATE", "UNSUPPORTED_ANCHOR_KIND"}
    assert all(row["record_ordinal"] == 3 and row["is_unreferenced"] and row["anchor_id"] == "bad-unused" for row in rows)
    assert len({row["input_issue_id"] for row in rows}) == 2
    assert len(csv_rows(input_issues_csv(bundle))) == 2
    assert bundle["input_accounting"]["anchors.csv"]["unreferenced_record_ordinals"] == [2, 3]


def test_related_source_is_distinct_from_issue_evidence_table(records, make_bundle):
    records["anchors.csv"][0]["participant_id"] = "other-person"
    bundle = make_bundle(records)
    assert validate_input_accounting(bundle) is bundle["input_accounting"]
    row, = build_input_issue_list(bundle)
    assert row["source_file"] == row["evidence_ref"]["source_file"] == "visits.csv"
    assert row["related_source_file"] == "anchors.csv" and row["related_record_ordinal"] == 1


def test_absent_accounting_stays_unavailable_and_exports_have_headers(records, make_bundle):
    bundle = make_bundle(records)
    del bundle["input_accounting"]
    assert validate_input_accounting(bundle) is None
    assert build_input_issue_list(bundle) == []
    assert csv_rows(worklist_csv(bundle)) == csv_rows(input_issues_csv(bundle)) == []
    assert b"input_issue_id" in input_issues_csv(bundle)


@pytest.mark.parametrize("field,value", [("record_count", True), ("record_count", -1), ("referenced_record_count", 2), ("issues", None), ("issues", [None]), ("unreferenced_record_ordinals", [1]), ("unreferenced_record_ordinals", [True])])
def test_malformed_accounting_table_is_structured(records, make_bundle, field, value):
    bundle = make_bundle(records)
    bundle["input_accounting"]["anchors.csv"][field] = value
    with pytest.raises(InputError) as caught:
        build_input_issue_list(bundle)
    assert caught.value.code == "ACCOUNTING_METADATA"


@pytest.mark.parametrize("field,value", [("record_ordinal", True), ("record_ordinal", 2), ("status", "PASS"), ("field", []), ("code", ""), ("source_file", "absent.csv"), ("related_record_ordinal", 20), ("evidence", None)])
def test_malformed_accounting_issue_is_structured(records, make_bundle, field, value):
    records["anchors.csv"][0]["participant_id"] = "other-person"
    bundle = make_bundle(records)
    bundle["input_accounting"]["visits.csv"]["issues"][0][field] = value
    with pytest.raises(InputError) as caught:
        input_issues_csv(bundle)
    assert caught.value.code == "ACCOUNTING_METADATA"


@pytest.mark.parametrize("value", [None, [], {"anchors.csv": {}}])
def test_accounting_must_be_complete_object_when_supplied(records, make_bundle, value):
    bundle = make_bundle(records)
    bundle["input_accounting"] = value
    with pytest.raises(InputError, match="Accounting"):
        build_worklist(bundle)


def test_worklist_rejects_semantically_invalid_bundle_and_bad_extension(records, make_bundle):
    records["visits.csv"][0]["actual_date"] = "2033-01-04"
    bundle = make_bundle(records)
    bundle["findings"][0]["evidence"][0]["sha256"] = "0" * 64
    with pytest.raises(InputError):
        build_worklist(bundle)
    bundle = make_bundle(records)
    bundle["findings"][0]["reason_codes"] = "OUTSIDE_INCLUSIVE_WINDOW"
    with pytest.raises(InputError) as caught:
        worklist_csv(bundle)
    assert caught.value.code == "WORKLIST_METADATA"
    bundle["findings"][0]["reason_codes"] = ["FUTURE_UNKNOWN_CODE"]
    assert "Review the supplied reason" in build_worklist(bundle)[0]["suggested_action"]


@pytest.mark.parametrize("value", ["=1+1", "+1", "-1", "@SUM(1,1)", "  =1+1", "\tformula", "\r\n=1+1", "\u00a0@danger", "\u200b=1+1", "\x01safe"])
def test_review_csv_protects_formula_and_control_prefixes_without_modifying_json(records, make_bundle, value):
    records["visits.csv"][0]["actual_date"] = "2033-01-04"
    bundle = make_bundle(records)
    bundle["findings"][0]["reason"] = value
    original = json.dumps(bundle, sort_keys=True)
    assert build_worklist(bundle)[0]["reason"] == value
    assert csv_rows(worklist_csv(bundle))[0]["reason"] == "'" + value
    assert json.dumps(bundle, sort_keys=True) == original


def test_input_issue_csv_protects_exact_source_ids_and_csv_roundtrips(records, make_bundle):
    records["anchors.csv"].append(dict(records["anchors.csv"][0], anchor_id="=source_formula", anchor_date="invalid", participant_id='a, "quoted"\nidentifier'))
    bundle = make_bundle(records)
    original = json.dumps(bundle, sort_keys=True)
    row, = build_input_issue_list(bundle)
    exported, = csv_rows(input_issues_csv(bundle))
    assert row["anchor_id"] == "=source_formula" and exported["anchor_id"] == "'=source_formula"
    assert exported["participant_id"] == 'a, "quoted"\nidentifier'
    assert json.loads(exported["evidence_ref"]) == row["evidence_ref"]
    assert json.dumps(bundle, sort_keys=True) == original


def test_issue_evidence_hash_and_identifier_shape_cannot_be_fabricated(records, make_bundle):
    records["anchors.csv"][0]["anchor_date"] = "invalid"
    bundle = make_bundle(records)
    evidence = bundle["input_accounting"]["anchors.csv"]["issues"][0]["evidence"]
    evidence["sha256"] = "f" * 64
    with pytest.raises(InputError) as caught:
        build_input_issue_list(bundle)
    assert caught.value.code == "ACCOUNTING_METADATA"
    bundle = make_bundle(records)
    bundle["input_accounting"]["anchors.csv"]["issues"][0]["evidence"]["raw_record"]["anchor_id"] = {"forged": "value"}
    with pytest.raises(InputError) as caught:
        build_input_issue_list(bundle)
    assert caught.value.code == "ACCOUNTING_METADATA"


@pytest.mark.parametrize("claim", ["zero_records", "unreferenced_evidence", "too_few_referenced"])
def test_accounting_cannot_contradict_records_observed_in_finding_evidence(records, make_bundle, claim):
    bundle = make_bundle(records)
    table = bundle["input_accounting"]["anchors.csv"]
    if claim == "zero_records":
        table.update(record_count=0, referenced_record_count=0, unreferenced_record_ordinals=[])
    elif claim == "unreferenced_evidence":
        table.update(referenced_record_count=0, unreferenced_record_ordinals=[1])
    else:
        # Conservation alone is insufficient when it contradicts observed refs.
        table.update(record_count=2, referenced_record_count=0, unreferenced_record_ordinals=[1, 2])
    with pytest.raises(InputError) as caught:
        build_worklist(bundle)
    assert caught.value.code == "ACCOUNTING_METADATA"
