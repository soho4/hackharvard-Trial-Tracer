"""Independently authored synthetic cases; expected labels never enter runtime."""

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
HEADERS = {
    "anchors.csv": "study_id,participant_id,site_id,anchor_id,anchor_code,anchor_kind,anchor_date".split(","),
    "visits.csv": "study_id,participant_id,site_id,visit_id,visit_code,event_kind,actual_date,visit_status,anchor_id,assignment_id".split(","),
    "assignments.csv": "assignment_id,study_id,participant_id,site_id,rule_version,schedule_code,mapping_status,mapping_note".split(","),
}


@pytest.fixture
def rule_bytes():
    return (ROOT / "rules/candidate_rule.json").read_bytes()


@pytest.fixture
def rule(rule_bytes):
    return json.loads(rule_bytes)


@pytest.fixture
def rule_sha256(rule_bytes):
    return hashlib.sha256(rule_bytes).hexdigest()


@pytest.fixture
def frozen_paths():
    return {name: ROOT / "fixtures/core_draft" / name for name in HEADERS}


@pytest.fixture
def records():
    common = {"study_id": "NCT04470427", "participant_id": "synthetic-never-bundled-817", "site_id": "synthetic-site-new"}
    return {
        "anchors.csv": [dict(common, anchor_id="anchor-new-817", anchor_code="OL_D1", anchor_kind="ACTUAL_VACCINATION", anchor_date="2032-12-24")],
        "visits.csv": [dict(common, visit_id="visit-new-817", visit_code="OL_D8", event_kind="SAFETY_PHONE_CALL", actual_date="2033-01-01", visit_status="COMPLETED", anchor_id="anchor-new-817", assignment_id="assignment-new-817")],
        "assignments.csv": [dict(common, assignment_id="assignment-new-817", rule_version="A10_DRAFT_2", schedule_code="TABLE21", mapping_status="DRAFT_SYNTHETIC", mapping_note="New authored synthetic test, no human approval.")],
    }


@pytest.fixture
def write_inputs(tmp_path):
    def write(records, *, headers=None, newline="\n", bom=False, directory=None):
        destination = directory or tmp_path
        destination.mkdir(parents=True, exist_ok=True)
        paths = {}
        for name, fields in (headers or HEADERS).items():
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator=newline)
            writer.writeheader()
            writer.writerows(records[name])
            paths[name] = destination / name
            paths[name].write_bytes((b"\xef\xbb\xbf" if bom else b"") + stream.getvalue().encode("utf-8"))
        return paths
    return write


@pytest.fixture
def make_bundle(write_inputs, rule, rule_sha256):
    def make(records):
        from trialtrace.exporter import build_bundle
        from trialtrace.importer import load_inputs

        return build_bundle(load_inputs(write_inputs(records)), rule, rule_sha256, mode="DRAFT_ENGINEERING")
    return make
