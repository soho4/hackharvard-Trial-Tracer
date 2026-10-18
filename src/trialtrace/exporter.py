"""Viewer-compatible evidence, canonical encoding and semantic validation."""

import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator

from . import __version__
from .engine import evaluate
from .errors import InputError
from .importer import HEADERS
from .relationships import parse_date

MAX_OUTPUT_BYTES = 2_000_000
SCHEMA_PATH = Path(__file__).with_name("evidence_bundle.schema.json")


def code_digest():
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    digest.update(SCHEMA_PATH.read_bytes())
    return digest.hexdigest()


def build_bundle(tables, rule, rule_sha256, *, mode=None, source_metadata=None):
    if not isinstance(rule_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", rule_sha256):
        raise InputError("RULE_HASH", "Rule digest must identify the actual rule bytes")
    result = evaluate(tables, rule, rule_sha256, mode=mode)
    loc = rule["source_locator"]
    source = {
        "url": rule["source_url"],
        "locator": f"Table {loc['table']}; printed pages {', '.join(map(str, loc['printed_pages']))}; PDF pages (1-based) {', '.join(map(str, loc['pdf_pages_one_indexed']))}",
        "pdf_sha256": None,
        "retrieval_status": "SOURCE_BYTES_NOT_SUPPLIED_TO_RUN",
    }
    if source_metadata is not None:
        if set(source_metadata) != {"pdf_sha256", "retrieval_status"}:
            raise InputError("SOURCE_METADATA", "Source metadata must contain only hash and retrieval status")
        source.update(source_metadata)
    bundle = {
        "schema_version": "trialtrace.evidence.v1", "data_kind": "SYNTHETIC", "clinical_validation": False,
        "producer": {"kind": "DEMO_ENGINE", "version": __version__, "code_sha256": code_digest()},
        "review_status": "PENDING_TEAM_SOURCE_REVIEW", "run_mode": mode,
        "source": source,
        "ruleset": {"id": rule["rule_id"], "version": rule["rule_version"], "sha256": rule_sha256},
        "input_files": [{key: table[key] for key in ("name", "display_name", "sha256", "bom", "byte_count")} for name, table in sorted(tables.items())],
        "limitations": [
            "DRAFT ENGINEERING ONLY: source interpretation is unreviewed and pending independent human source review and integrator acceptance.",
            "Synthetic inputs only. No clinical validation or clinical/regulatory determination. A potential deviation requires human review.",
            "PASS means only this supported timing check passed under the stated draft rule; missing records never imply missed activities.",
            "File hashes identify supplied bytes and internal references; they do not authenticate source data or human review.",
            *rule["interpretation_notes"],
        ],
        **result,
    }
    digest = hashlib.sha256(b"trialtrace.bundle.v1\0")
    for chunk in json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).iterencode(bundle):
        digest.update(chunk.encode("utf-8"))
    bundle["run_id"] = digest.hexdigest()
    validate_bundle(bundle)
    return bundle


def validate_bundle(bundle):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(bundle))
    if errors:
        first = errors[0]
        raise InputError("EXPORT_SCHEMA", first.message, path=list(first.absolute_path))
    files, ids = {}, set()
    for item in bundle["input_files"]:
        if item["name"] in files:
            raise InputError("DUPLICATE_FILE", "Input-file names must be unique")
        files[item["name"]] = item["sha256"]
    if bundle["producer"]["kind"] == "DEMO_ENGINE":
        if set(files) != set(HEADERS):
            raise InputError("EVIDENCE_ROLES", "Engine exports require exactly the three canonical input roles")
        if bundle.get("run_mode") != "DRAFT_ENGINEERING" or bundle["review_status"] != "PENDING_TEAM_SOURCE_REVIEW":
            raise InputError("EXPORT_MODE", "This core exports explicit draft mode only; reviewed release is blocked")

    def check_evidence(item):
        if item["source_file"] not in files or item["sha256"] != files[item["source_file"]]:
            raise InputError("EVIDENCE_HASH", "Evidence must reference a declared file with the exact full SHA-256")
        if type(item["record_ordinal"]) is not int or item["record_ordinal"] < 1:
            raise InputError("EVIDENCE_ORDINAL", "Evidence requires a positive logical record ordinal")

    for finding in bundle["findings"]:
        if finding["finding_id"] in ids:
            raise InputError("DUPLICATE_FINDING", "Finding IDs must be unique")
        ids.add(finding["finding_id"])
        calculation, status = finding["calculation"], finding["status"]
        if status in ("DATA_QUERY", "NOT_EVALUABLE"):
            if calculation is not None:
                raise InputError("UNRESOLVED_CALCULATION", "Unresolved findings require null calculation")
        else:
            if calculation is None:
                raise InputError("MISSING_CALCULATION", "Timing outcomes require a calculation")
            try:
                dates = {key: parse_date(calculation[key]) for key in ("target", "earliest", "latest", "actual")}
            except ValueError as exc:
                raise InputError("CALCULATION_DATE", "Calculation contains an invalid calendar date") from exc
            if not dates["earliest"] <= dates["target"] <= dates["latest"]:
                raise InputError("CALCULATION_BOUNDS", "Target must lie inside the declared interval")
            distance = max((dates["earliest"] - dates["actual"]).days, (dates["actual"] - dates["latest"]).days, 0)
            if type(calculation["days_outside"]) is not int or calculation["days_outside"] != distance:
                raise InputError("CALCULATION_DISTANCE", "days_outside disagrees with the actual date and bounds")
            if (status == "PASS") != (distance == 0):
                raise InputError("OUTCOME_CALCULATION", "Outcome and calculation disagree")
        for item in finding["evidence"]:
            check_evidence(item)
    # These additional diagnostics are outside the viewer schema but also carry evidence.
    for table in bundle.get("input_accounting", {}).values():
        for issue in table["issues"]:
            check_evidence(issue["evidence"])
    return None


def serialize_bundle(bundle):
    validate_bundle(bundle)
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    output = bytearray()
    for chunk in encoder.iterencode(bundle):
        encoded = chunk.encode("utf-8")
        if len(output) + len(encoded) + 1 > MAX_OUTPUT_BYTES:
            raise InputError("OUTPUT_SIZE_LIMIT", "Full report exceeds the 2,000,000-byte viewer limit; no evidence was truncated")
        output.extend(encoded)
    output.extend(b"\n")
    return bytes(output)
