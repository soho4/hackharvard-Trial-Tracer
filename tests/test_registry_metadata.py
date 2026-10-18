"""Optional public metadata is bounded and explicit; no fallback or approval."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from conftest import ROOT
from trialtrace.errors import InputError
from trialtrace.registry_metadata import MAX_REGISTRY_BYTES, load_registry_snapshot


@pytest.fixture
def snapshot():
    return json.loads((ROOT / "docs/trialtrace/review/g3_source/registry_snapshot.json").read_text())


def write_snapshot(tmp_path, value):
    path = tmp_path / "public-snapshot.json"
    path.write_text(json.dumps(value, ensure_ascii=True))
    return path


def test_actual_public_snapshot_is_preserved_without_new_claims():
    path = ROOT / "docs/trialtrace/review/g3_source/registry_snapshot.json"
    raw = path.read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    loaded = load_registry_snapshot(path)
    assert loaded == json.loads(raw)
    assert loaded["is_participant_event_data"] is False
    assert loaded["protocol_document"]["clinical_validation"] is False
    assert loaded["protocol_document"]["source_interpretation_review"] == "BLOCKED_PENDING_HUMAN_REVIEW"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("kind", ["missing", "directory", "unreadable"])
def test_file_access_is_structured_without_invented_facts(tmp_path, monkeypatch, kind):
    path = tmp_path / "snapshot.json"
    if kind == "directory":
        path.mkdir()
    elif kind == "unreadable":
        def denied(*_args, **_kwargs):
            raise PermissionError("synthetic access denial")
        monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(InputError) as error:
        load_registry_snapshot(path)
    assert error.value.code == "REGISTRY_ACCESS"


@pytest.mark.parametrize("raw,code", [
    (b"{", "REGISTRY_JSON"),
    (b"", "REGISTRY_JSON"),
    (b"\xff", "REGISTRY_ENCODING"),
    (b'{"a":1,"a":2}', "REGISTRY_JSON"),
    (b'{"nested":{"a":1,"a":2}}', "REGISTRY_JSON"),
    (b'{"number":NaN}', "REGISTRY_JSON"),
    (b'{"number":Infinity}', "REGISTRY_JSON"),
    (b'{"number":-Infinity}', "REGISTRY_JSON"),
    (b'{"number":1e999}', "REGISTRY_JSON"),
    (b'{"text":"\\ud800"}', "REGISTRY_ENCODING"),
    (b'{"\\udfff":"value"}', "REGISTRY_ENCODING"),
    (b"[" * 33 + b"0" + b"]" * 33, "REGISTRY_DEPTH"),
    (b"[]", "REGISTRY_FIELDS"),
    (b"null", "REGISTRY_FIELDS"),
])
def test_malformed_json_is_a_structured_failure(tmp_path, raw, code):
    path = tmp_path / "malformed.json"
    path.write_bytes(raw)
    with pytest.raises(InputError) as error:
        load_registry_snapshot(path)
    assert error.value.code == code


def test_file_limit_accepts_exact_boundary_then_rejects_next_byte(tmp_path, snapshot):
    raw = json.dumps(snapshot).encode()
    raw += b" " * (MAX_REGISTRY_BYTES - len(raw))
    path = tmp_path / "bounded.json"
    path.write_bytes(raw)
    assert load_registry_snapshot(path) == snapshot
    path.write_bytes(raw + b" ")
    with pytest.raises(InputError) as error:
        load_registry_snapshot(path)
    assert error.value.code == "REGISTRY_SIZE_LIMIT"


def test_quotes_brackets_and_valid_unicode_do_not_trigger_false_depth_errors(tmp_path, snapshot):
    snapshot["extra_public_note"] = '["' * 100 + ' literal \\" brackets 研究 🧪 '
    assert load_registry_snapshot(write_snapshot(tmp_path, snapshot)) == snapshot


@pytest.mark.parametrize("path,value,code", [
    (("schema_version",), "other.v1", "REGISTRY_IDENTITY"),
    (("is_participant_event_data",), 0, "REGISTRY_IDENTITY"),
    (("is_participant_event_data",), True, "REGISTRY_IDENTITY"),
    (("source",), [], "REGISTRY_FIELDS"),
    (("study",), None, "REGISTRY_FIELDS"),
    (("source", "api_url"), "https://example.com/api/NCT04470427", "REGISTRY_IDENTITY"),
    (("source", "study_url"), "https://clinicaltrials.gov/study/NCT00000000", "REGISTRY_IDENTITY"),
    (("source", "http_status"), "200", "REGISTRY_IDENTITY"),
    (("source", "transport_tls_verified"), 1, "REGISTRY_IDENTITY"),
    (("source", "snapshot_not_live_feed"), False, "REGISTRY_IDENTITY"),
    (("source", "response_byte_count"), True, "REGISTRY_FIELDS"),
    (("source", "response_byte_count"), 0, "REGISTRY_FIELDS"),
    (("source", "response_sha256"), "abc", "REGISTRY_FIELDS"),
    (("study", "nct_id"), "NCT00000000", "REGISTRY_IDENTITY"),
    (("study", "protocol_id"), "different-protocol", "REGISTRY_IDENTITY"),
    (("study", "overall_status"), [], "REGISTRY_FIELDS"),
    (("study", "lead_sponsor"), "", "REGISTRY_FIELDS"),
    (("study", "lead_sponsor"), "Sponsor\nInjected line", "REGISTRY_FIELDS"),
    (("study", "last_update_posted"), "2024-02-30", "REGISTRY_DATE"),
    (("study", "last_update_posted"), "2024-3-21", "REGISTRY_DATE"),
    (("study", "last_update_posted"), "2024-03-21T00:00:00Z", "REGISTRY_DATE"),
    (("source", "fetched_at_utc"), "2026-02-30T12:00:00Z", "REGISTRY_DATE"),
    (("source", "fetched_at_utc"), "2026-10-18", "REGISTRY_DATE"),
    (("source", "fetched_at_utc"), "2026-10-18T12:00:00", "REGISTRY_DATE"),
    (("source", "fetched_at_utc"), "2026-10-18T12:00:00+05:00", "REGISTRY_DATE"),
    (("protocol_document", "url"), "https://example.com/other.pdf", "REGISTRY_IDENTITY"),
    (("protocol_document", "clinical_validation"), True, "REGISTRY_IDENTITY"),
    (("protocol_document", "source_interpretation_review"), "APPROVED", "REGISTRY_IDENTITY"),
])
def test_consumed_fields_and_declared_identity_are_checked(tmp_path, snapshot, path, value, code):
    changed = deepcopy(snapshot)
    target = changed
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(InputError) as error:
        load_registry_snapshot(write_snapshot(tmp_path, changed))
    assert error.value.code == code
    assert error.value.context["field"] == ".".join(path)


@pytest.mark.parametrize("field", ["source", "study", "schema_version"])
def test_missing_required_sections_are_structured(tmp_path, snapshot, field):
    del snapshot[field]
    with pytest.raises(InputError):
        load_registry_snapshot(write_snapshot(tmp_path, snapshot))


@pytest.mark.parametrize("timestamp", ["2026-10-18T08:24:23Z", "2026-10-18T08:24:23.123456+00:00"])
def test_explicit_valid_utc_timestamps_preserve_original_text(tmp_path, snapshot, timestamp):
    snapshot["source"]["fetched_at_utc"] = timestamp
    assert load_registry_snapshot(write_snapshot(tmp_path, snapshot))["source"]["fetched_at_utc"] == timestamp
