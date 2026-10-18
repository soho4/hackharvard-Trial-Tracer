"""G1-only identity, relationship and source-accounting checks."""

import pytest

from trialtrace.importer import load_inputs
from trialtrace.relationships import inspect_inputs


def inspect(records, write_inputs):
    return inspect_inputs(load_inputs(write_inputs(records)))


def test_valid_relationships_account_for_every_row(records, write_inputs):
    result = inspect(records, write_inputs)
    assert len(result["visits"]) == 1
    assert result["visits"][0]["problems"] == []
    assert len(result["visits"][0]["evidence"]) == 3
    for name, entry in result["input_accounting"].items():
        assert entry["record_count"] == 1
        assert entry["referenced_record_count"] == 1
        assert entry["unreferenced_record_ordinals"] == []
        assert entry["issues"] == []
    assert result["visits"][0]["joined"]["anchors.csv"]["raw_record"] == records["anchors.csv"][0]


@pytest.mark.parametrize("table", ["anchors.csv", "assignments.csv", "visits.csv"])
def test_duplicate_even_if_identical_is_ambiguous_with_both_evidence_rows(records, write_inputs, table):
    records[table].append(dict(records[table][0]))
    result = inspect(records, write_inputs)
    assert result["input_accounting"][table]["record_count"] == 2
    assert {issue["record_ordinal"] for issue in result["input_accounting"][table]["issues"]} == {1, 2}
    assert len(result["visits"]) == (2 if table == "visits.csv" else 1)
    for visit in result["visits"]:
        assert any(problem["status"] == "DATA_QUERY" for problem in visit["problems"])
        evidence = [item for item in visit["evidence"] if item["source_file"] == table]
        assert {item["record_ordinal"] for item in evidence} == {1, 2}


@pytest.mark.parametrize("table", ["anchors.csv", "assignments.csv"])
@pytest.mark.parametrize("field", ["study_id", "participant_id", "site_id"])
def test_wrong_identity_is_query_with_actual_conflicting_evidence(records, write_inputs, table, field):
    records[table][0][field] = "another-identity"
    result = inspect(records, write_inputs)
    visit = result["visits"][0]
    assert any(problem["status"] == "DATA_QUERY" for problem in visit["problems"])
    assert any(item["source_file"] == table and item["raw_record"][field] == "another-identity" for item in visit["evidence"])


@pytest.mark.parametrize("table", ["anchors.csv", "assignments.csv"])
def test_missing_reference_keeps_visit_without_fictional_source_row(records, write_inputs, table):
    records[table] = []
    result = inspect(records, write_inputs)
    visit = result["visits"][0]
    assert visit["record"]["raw_record"] == records["visits.csv"][0]
    assert any(problem["status"] == "DATA_QUERY" for problem in visit["problems"])
    assert visit["joined"][table] is None
    assert all(item["source_file"] != table for item in visit["evidence"])


@pytest.mark.parametrize("field", ["visit_id", "participant_id", "site_id", "anchor_id", "assignment_id"])
@pytest.mark.parametrize("bad", ["", " spaced "])
def test_blank_or_spaced_identity_preserved_as_query(records, write_inputs, field, bad):
    records["visits.csv"][0][field] = bad
    result = inspect(records, write_inputs)
    visit = result["visits"][0]
    assert visit["record"]["raw_record"][field] == bad
    assert any(problem["status"] == "DATA_QUERY" for problem in visit["problems"])


def test_unreferenced_invalid_rows_have_accounted_ordinals_and_issues(records, write_inputs):
    records["anchors.csv"].append(dict(records["anchors.csv"][0], anchor_id="unused", anchor_date="invalid"))
    records["assignments.csv"].append(dict(records["assignments.csv"][0], assignment_id="unused", participant_id=""))
    result = inspect(records, write_inputs)
    assert result["visits"][0]["problems"] == []
    for name in ("anchors.csv", "assignments.csv"):
        entry = result["input_accounting"][name]
        assert entry["record_count"] == 2
        assert entry["referenced_record_count"] == 1
        assert entry["unreferenced_record_ordinals"] == [2]
        assert {issue["record_ordinal"] for issue in entry["issues"]} == {2}


def test_multiline_records_use_logical_ordinals_in_relationship_evidence(records, write_inputs):
    records["assignments.csv"][0]["mapping_note"] = "synthetic line one\nline two"
    records["assignments.csv"].insert(0, dict(records["assignments.csv"][0], assignment_id="unused"))
    result = inspect(records, write_inputs)
    row = next(item for item in result["visits"][0]["evidence"] if item["source_file"] == "assignments.csv")
    assert row["record_ordinal"] == 2
    assert row["raw_record"]["mapping_note"] == "synthetic line one\nline two"
