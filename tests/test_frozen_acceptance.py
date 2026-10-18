"""Use the immutable pre-implementation answer key only in this test harness."""

from collections import Counter
import hashlib
import json

from conftest import ROOT
from trialtrace.exporter import build_bundle, validate_bundle
from trialtrace.importer import load_inputs


def test_frozen_hand_cases(frozen_paths, rule, rule_bytes, rule_sha256):
    expected = json.loads((ROOT / "fixtures/core_draft/expected.json").read_text())
    assert hashlib.sha256(rule_bytes).hexdigest() == expected["rule_sha256"]
    bundle = build_bundle(load_inputs(frozen_paths), rule, rule_sha256, mode="DRAFT_ENGINEERING")
    actual = [{key: finding[key] for key in ("visit_id", "status", "calculation")} for finding in bundle["findings"]]
    assert actual == expected["findings"]
    assert Counter(finding["status"] for finding in bundle["findings"]) == expected["expected_totals"]
    assert len(bundle["findings"]) == 10
    assert bundle["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"
    assert bundle["clinical_validation"] is False
    assert bundle["run_mode"] == "DRAFT_ENGINEERING"
    assert bundle["producer"]["kind"] == "DEMO_ENGINE"
    assert validate_bundle(bundle) is None
