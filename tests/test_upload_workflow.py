"""Real-byte upload/CLI parity; source hashing is provenance, never approval."""

import hashlib
import json
import os
import subprocess
import sys

import pytest

from conftest import ROOT
from trialtrace.errors import InputError
from trialtrace.importer import load_inputs, parse_table
from trialtrace.source import hash_source_pdf
from trialtrace.workflow import check_uploads


def test_parse_uploaded_bytes_matches_actual_file_parser(records, write_inputs):
    records["assignments.csv"][0]["mapping_note"] = 'Synthetic note, "quoted"\r\nsecond line 🧪'
    paths = write_inputs(records, bom=True, newline="\r\n")
    loaded = load_inputs(paths)
    for name, path in paths.items():
        assert parse_table(path.read_bytes(), name, path.name) == loaded[name]


@pytest.mark.parametrize("with_source", [False, True])
def test_upload_output_is_byte_identical_to_actual_cli_with_same_display_names(records, write_inputs, rule, rule_sha256, tmp_path, with_source):
    original = write_inputs(records)
    paths, uploads = {}, {}
    for index, (role, path) in enumerate(original.items()):
        target = tmp_path / f"role-{index}" / "same-upload.csv"
        target.parent.mkdir()
        target.write_bytes(path.read_bytes())
        paths[role] = target
        uploads[role] = (target.name, target.read_bytes())
    source_path, source_metadata = None, None
    if with_source:
        # Deliberately artificial bytes only exercise byte provenance, not PDF
        # identity, source review, or clinical correctness.
        source_path = tmp_path / "synthetic-source-bytes.pdf"
        source_path.write_bytes(b"%PDF-1.7\nSYNTHETIC HASHING TEST ONLY\n" + b"z" * 140000)
        source_metadata = hash_source_pdf(source_path)
    bundle, encoded = check_uploads(uploads, rule, rule_sha256, draft_confirmed=True, source_metadata=source_metadata)
    output = tmp_path / "actual-cli.json"
    command = [sys.executable, "-m", "trialtrace.cli"]
    for role in ("anchors", "visits", "assignments"):
        command.extend(["--" + role, str(paths[role + ".csv"])])
    command.extend(["--rule", str(ROOT / "rules/candidate_rule.json"), "--draft-synthetic", "--output", str(output)])
    if source_path is not None:
        command.extend(["--source-pdf", str(source_path)])
    completed = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), capture_output=True, text=True, timeout=20)
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == encoded
    assert json.loads(encoded) == bundle
    assert {item["name"] for item in bundle["input_files"]} == set(uploads)
    assert all(item["display_name"] == "same-upload.csv" for item in bundle["input_files"])
    assert bundle["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"
    assert bundle["clinical_validation"] is False


def test_uploads_require_explicit_confirmation(records, write_inputs, rule, rule_sha256):
    uploads = {name: (path.name, path.read_bytes()) for name, path in write_inputs(records).items()}
    with pytest.raises(InputError) as error:
        check_uploads(uploads, rule, rule_sha256)
    assert error.value.code == "SOURCE_REVIEW_REQUIRED"


@pytest.mark.parametrize("missing", ["absent", "none"])
def test_missing_upload_role_is_structured_failure(records, write_inputs, rule, rule_sha256, missing):
    uploads = {name: (path.name, path.read_bytes()) for name, path in write_inputs(records).items()}
    if missing == "absent":
        uploads.pop("anchors.csv")
    else:
        uploads["anchors.csv"] = None
    with pytest.raises(InputError) as error:
        check_uploads(uploads, rule, rule_sha256, draft_confirmed=True)
    assert error.value.code == "INPUT_ROLES"


@pytest.mark.parametrize("raw,code", [(b"bad,header\ninvalid,row\n", "INVALID_HEADER"), (b"\xff", "INVALID_UTF8"), (b"x" * 1000001, "INPUT_SIZE_LIMIT")])
def test_malformed_uploaded_bytes_are_not_partial_success(records, write_inputs, rule, rule_sha256, raw, code):
    uploads = {name: (path.name, path.read_bytes()) for name, path in write_inputs(records).items()}
    uploads["visits.csv"] = ("replacement.csv", raw)
    with pytest.raises(InputError) as error:
        check_uploads(uploads, rule, rule_sha256, draft_confirmed=True)
    assert error.value.code == code


def test_source_pdf_hash_covers_every_exact_byte_without_claiming_identity(tmp_path):
    raw = b"%PDF-1.7\nSYNTHETIC HASH TEST\n" + b"0123456789" * 20000
    source = tmp_path / "synthetic-bytes.pdf"
    source.write_bytes(raw)
    metadata = hash_source_pdf(source)
    assert metadata["pdf_sha256"] == hashlib.sha256(raw).hexdigest()
    assert metadata["retrieval_status"] == "LOCAL_PDF_BYTES_HASHED_IDENTITY_NOT_CHECKED_BY_RUNTIME"
    source.write_bytes(raw[:-1] + b"x")
    assert hash_source_pdf(source)["pdf_sha256"] != metadata["pdf_sha256"]


def test_non_pdf_source_bytes_fail_explicitly(tmp_path):
    source = tmp_path / "incorrect-source.pdf"
    source.write_bytes(b"This is not a PDF header.")
    with pytest.raises(InputError) as error:
        hash_source_pdf(source)
    assert error.value.code == "SOURCE_PDF"
