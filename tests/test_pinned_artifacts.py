"""Byte pins copied from the supplied v4 PACKAGE_MANIFEST, not regenerated outputs."""

import hashlib
from importlib.resources import files

from conftest import ROOT


SCHEMA_SHA256 = "706c2b68086f1c9d38ac5ddbc37653e6f1da45d7d595eabff194c3e9737abee0"
RULE_SHA256 = "f36336df90a1793a80b92f48ce273488a091547110856bdcc602587ddad9e7f0"


def test_repository_and_runtime_packaged_schema_are_the_exact_pinned_contract():
    contract = (ROOT / "contracts/evidence_bundle.schema.json").read_bytes()
    packaged = files("trialtrace").joinpath("evidence_bundle.schema.json").read_bytes()
    assert hashlib.sha256(contract).hexdigest() == SCHEMA_SHA256
    assert hashlib.sha256(packaged).hexdigest() == SCHEMA_SHA256
    assert packaged == contract


def test_candidate_rule_remains_immutable_pending_separate_review():
    assert hashlib.sha256((ROOT / "rules/candidate_rule.json").read_bytes()).hexdigest() == RULE_SHA256
