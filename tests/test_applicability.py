from copy import deepcopy

import pytest

from trialtrace.errors import InputError
from trialtrace.exporter import build_bundle
from trialtrace.importer import load_inputs


def only_finding(bundle, status):
    assert len(bundle["findings"]) == 1
    finding = bundle["findings"][0]
    assert finding["status"] == status
    assert finding["reason"]
    if status in ("DATA_QUERY", "NOT_EVALUABLE"):
        assert finding["calculation"] is None
    return finding


def test_new_synthetic_identifier_and_year_boundary(records, make_bundle):
    finding = only_finding(make_bundle(records), "PASS")
    assert finding["visit_id"] == "visit-new-817"
    assert finding["participant_id"] == "synthetic-never-bundled-817"
    assert finding["calculation"] == {"target": "2032-12-31", "earliest": "2032-12-31", "latest": "2033-01-03", "actual": "2033-01-01", "days_outside": 0}


@pytest.mark.parametrize("table,field", [
    ("visits.csv", "study_id"), ("visits.csv", "participant_id"), ("visits.csv", "site_id"),
    ("visits.csv", "visit_id"), ("visits.csv", "anchor_id"), ("visits.csv", "assignment_id"),
    ("anchors.csv", "anchor_id"), ("assignments.csv", "assignment_id"),
])
@pytest.mark.parametrize("bad", ["", " ", " leading", "trailing "])
def test_identity_is_never_silently_trimmed_or_inferred(records, make_bundle, table, field, bad):
    records[table][0][field] = bad
    finding = only_finding(make_bundle(records), "DATA_QUERY")
    assert any(evidence["source_file"] == "visits.csv" for evidence in finding["evidence"])


@pytest.mark.parametrize("table,field", [
    ("anchors.csv", "study_id"), ("anchors.csv", "participant_id"), ("anchors.csv", "site_id"),
    ("assignments.csv", "study_id"), ("assignments.csv", "participant_id"), ("assignments.csv", "site_id"),
])
def test_wrong_study_person_or_site_never_supports_arithmetic(records, make_bundle, table, field):
    records[table][0][field] = "different-case-sensitive-identity"
    finding = only_finding(make_bundle(records), "DATA_QUERY")
    conflicting = [item for item in finding["evidence"] if item["source_file"] == table]
    assert len(conflicting) == 1
    assert conflicting[0]["raw_record"][field] == "different-case-sensitive-identity"


@pytest.mark.parametrize("table", ["anchors.csv", "assignments.csv"])
def test_missing_reference_does_not_fabricate_evidence(records, make_bundle, table):
    records[table] = []
    finding = only_finding(make_bundle(records), "DATA_QUERY")
    assert all(item["source_file"] != table for item in finding["evidence"])
    assert sum(item["source_file"] == "visits.csv" for item in finding["evidence"]) == 1


@pytest.mark.parametrize("table", ["anchors.csv", "assignments.csv", "visits.csv"])
@pytest.mark.parametrize("conflicting", [False, True])
def test_identical_and_conflicting_duplicates_remain_ambiguous(records, make_bundle, table, conflicting):
    duplicate = deepcopy(records[table][0])
    if conflicting:
        duplicate["participant_id"] = "different-synthetic-person"
    records[table].append(duplicate)
    findings = make_bundle(records)["findings"]
    assert len(findings) == (2 if table == "visits.csv" else 1)
    assert len({finding["finding_id"] for finding in findings}) == len(findings)
    for finding in findings:
        assert finding["status"] == "DATA_QUERY"
        assert finding["calculation"] is None
        assert len([item for item in finding["evidence"] if item["source_file"] == table]) == 2


@pytest.mark.parametrize("table,field,value", [
    ("visits.csv", "event_kind", "CLINIC_VISIT"), ("visits.csv", "visit_code", "OL_D15"),
    ("anchors.csv", "anchor_kind", "PARTICIPANT_DECISION"), ("anchors.csv", "anchor_code", "DECISION"),
    ("assignments.csv", "rule_version", "A10_FUTURE"), ("assignments.csv", "schedule_code", "TABLE22"),
    ("assignments.csv", "mapping_status", "UNRESOLVED"), ("assignments.csv", "mapping_status", "DEMO_REVIEWED"),
])
def test_unsupported_or_unreviewed_scope_abstains(records, make_bundle, table, field, value):
    records[table][0][field] = value
    finding = only_finding(make_bundle(records), "NOT_EVALUABLE")
    assert any(item["source_file"] == table and item["raw_record"][field] == value for item in finding["evidence"])


def test_unknown_completion_does_not_become_complete_from_date(records, make_bundle):
    records["visits.csv"][0]["visit_status"] = "UNKNOWN"
    only_finding(make_bundle(records), "DATA_QUERY")


@pytest.mark.parametrize("table,field", [("anchors.csv", "anchor_date"), ("visits.csv", "actual_date")])
@pytest.mark.parametrize("date", ["", "20330101", "01/01/2033", "2033-1-01", "2033-01-1", "2033-02-29", "2033-04-31", "2033-01-01T00:00:00Z", " 2033-01-01", "2033-01-01 ", "0000-01-01"])
def test_bad_date_shapes_and_calendar_values_are_row_queries(records, make_bundle, table, field, date):
    records[table][0][field] = date
    finding = only_finding(make_bundle(records), "DATA_QUERY")
    assert any(item["source_file"] == table and item["raw_record"][field] == date for item in finding["evidence"])


def test_overflow_becomes_row_query(records, make_bundle):
    records["anchors.csv"][0]["anchor_date"] = "9999-12-29"
    only_finding(make_bundle(records), "DATA_QUERY")


def test_identity_breakage_precedes_unsupported_scope_and_keeps_both_reasons(records, make_bundle):
    records["anchors.csv"][0]["participant_id"] = "wrong-person"
    records["visits.csv"][0]["event_kind"] = "CLINIC_VISIT"
    finding = only_finding(make_bundle(records), "DATA_QUERY")
    assert len(finding["reason_codes"]) >= 2


def test_unknown_anchor_kind_is_not_reported_as_a_missing_anchor(records, make_bundle):
    records["anchors.csv"][0]["anchor_kind"] = "DECISION"
    finding = only_finding(make_bundle(records), "NOT_EVALUABLE")
    assert "missing" not in finding["reason"].lower()


def test_all_rows_accounted_for_including_unreferenced_bad_rows(records, make_bundle):
    records["anchors.csv"].append(dict(records["anchors.csv"][0], anchor_id="unreferenced-anchor", anchor_date="broken"))
    records["assignments.csv"].append(dict(records["assignments.csv"][0], assignment_id="unreferenced-assignment", participant_id=" "))
    bundle = make_bundle(records)
    only_finding(bundle, "PASS")
    accounting = bundle["input_accounting"]
    assert set(accounting) == set(records)
    for name, rows in records.items():
        assert accounting[name]["record_count"] == len(rows)
    for name in ("anchors.csv", "assignments.csv"):
        assert any(issue["record_ordinal"] == 2 for issue in accounting[name]["issues"])


def test_empty_visits_are_empty_evaluations_with_input_accounting(records, make_bundle):
    records["visits.csv"] = []
    bundle = make_bundle(records)
    assert bundle["findings"] == []
    assert bundle["input_accounting"]["visits.csv"]["record_count"] == 0
    assert bundle["input_accounting"]["anchors.csv"]["record_count"] == 1
    assert bundle["input_accounting"]["assignments.csv"]["record_count"] == 1


def test_reviewed_mode_requires_real_external_prerequisites(records, write_inputs, rule, rule_sha256):
    records["assignments.csv"][0]["mapping_status"] = "DEMO_REVIEWED"
    with pytest.raises(InputError) as error:
        build_bundle(load_inputs(write_inputs(records)), rule, rule_sha256, mode="REVIEWED_SYNTHETIC_DEMO")
    assert error.value.code


def test_draft_mapping_cannot_auto_promote(records, write_inputs, rule, rule_sha256):
    with pytest.raises(InputError):
        build_bundle(load_inputs(write_inputs(records)), rule, rule_sha256, mode="REVIEWED_SYNTHETIC_DEMO")
