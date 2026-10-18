"""Explicit wide-CSV mapping. No vendor certification, inferred joins or source approval."""
import csv
import hashlib
import io
import json
import zipfile

from .engine import canonical, validate_rule
from .errors import InputError
from .importer import HEADERS, MAX_BYTES, MAX_CELL, MAX_RECORDS, _logical_records, parse_table
from .workflow import check_uploads

FIELDS = {
    "study_id": "Study identifier",
    "participant_id": "Participant identifier",
    "site_id": "Site identifier",
    "visit_id": "Safety-call record identifier",
    "anchor_id": "Vaccination record identifier",
    "anchor_date": "Actual vaccination date",
    "actual_date": "Actual safety-call date",
    "visit_status": "Safety-call completion status",
}
MAX_COLUMNS = 64
MAX_PACKAGE_BYTES = 5_000_000


def inspect_spreadsheet(raw, display_name="source.csv"):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise InputError("INPUT_SIZE_LIMIT", "Supply a CSV of at most 1,000,000 bytes")
    if b"\x00" in raw:
        raise InputError("NUL_BYTE", "NUL bytes are not accepted")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("INVALID_UTF8", "Input is not UTF-8") from exc
    if not text.strip():
        raise InputError("EMPTY_FILE", "The spreadsheet is empty")
    headers, rows = None, []
    for ordinal, raw_csv in enumerate(_logical_records(text, "source.csv")):
        try:
            values = next(csv.reader(io.StringIO(raw_csv, newline=""), strict=True))
        except (csv.Error, StopIteration) as exc:
            raise InputError("CSV_PARSE", "Malformed CSV record", record_ordinal=ordinal) from exc
        if any(len(value) > MAX_CELL for value in values):
            raise InputError("CELL_SIZE_LIMIT", "Cell exceeds 10,000 characters", record_ordinal=ordinal)
        if headers is None:
            if not 1 <= len(values) <= MAX_COLUMNS or len(values) != len(set(values)) or any(not v.strip() or v != v.strip() for v in values):
                raise InputError("INVALID_HEADER", "Use 1–64 unique nonblank column names without surrounding whitespace")
            headers = values
        else:
            if ordinal > MAX_RECORDS:
                raise InputError("RECORD_LIMIT", "Spreadsheet exceeds 500 data records")
            if len(values) != len(headers):
                raise InputError("ROW_WIDTH", "Row width does not match header", record_ordinal=ordinal)
            rows.append({"record_ordinal": ordinal, "raw_record": dict(zip(headers, values)), "raw_csv": raw_csv})
    return {"headers": headers, "records": rows, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "bom": raw.startswith(b"\xef\xbb\xbf"), "display_name": "".join(c for c in str(display_name) if c.isprintable())[:200] or "source.csv"}


def prepare_spreadsheet(raw, display_name, mapping, completed_value, rule, rule_sha256, *, scope_confirmed=False):
    """Every input row becomes one row in each canonical table; no filtering/deduplication."""
    if scope_confirmed is not True:
        raise InputError("PREPARATION_SCOPE", "Confirm synthetic data, column meanings and draft Table 21 scope")
    validate_rule(rule)
    if not isinstance(rule_sha256, str) or len(rule_sha256) != 64 or any(c not in "0123456789abcdef" for c in rule_sha256):
        raise InputError("RULE_HASH", "Supply the exact rule-file SHA-256")
    sheet = inspect_spreadsheet(raw, display_name)
    if not isinstance(mapping, dict) or set(mapping) != set(FIELDS) or any(not isinstance(v, str) or v not in sheet["headers"] for v in mapping.values()):
        raise InputError("COLUMN_MAPPING", "Explicitly choose one existing source column for each required field")
    if len(set(mapping.values())) != len(mapping):
        raise InputError("COLUMN_REUSED", "Different meanings must use different source columns")
    if not isinstance(completed_value, str) or not completed_value.strip() or len(completed_value) > MAX_CELL:
        raise InputError("COMPLETION_MAPPING", "Choose the exact source value meaning the call occurred and was completed")
    if completed_value not in {r["raw_record"][mapping["visit_status"]] for r in sheet["records"]}:
        raise InputError("COMPLETION_MAPPING", "The selected completed-call value is absent from this file")
    spec = {"schema_version": "trialtrace.preparation.v1", "source_sha256": sheet["sha256"], "columns": mapping,
            "completed_value": completed_value, "rule_sha256": rule_sha256, "scope": "USER_DECLARED_SYNTHETIC_TABLE21_ONLY"}
    prep_id = hashlib.sha256(canonical(spec)).hexdigest()
    generated = {name: [] for name in HEADERS}
    lineage = []
    for rec in sheet["records"]:
        ordinal, original = rec["record_ordinal"], rec["raw_record"]
        values = {field: original[column] for field, column in mapping.items()}
        common = {field: values[field] for field in ("study_id", "participant_id", "site_id")}
        assignment = "PREP-" + str(ordinal)
        generated["anchors.csv"].append(dict(common, anchor_id=values["anchor_id"], anchor_code=rule["anchor_code"],
                                              anchor_kind=rule["anchor_kind"], anchor_date=values["anchor_date"]))
        generated["visits.csv"].append(dict(common, visit_id=values["visit_id"], visit_code=rule["supported_visit_code"],
                                             event_kind=rule["event_kind"], actual_date=values["actual_date"],
                                             visit_status="COMPLETED" if values["visit_status"] == completed_value else "UNCONFIRMED",
                                             anchor_id=values["anchor_id"], assignment_id=assignment))
        generated["assignments.csv"].append(dict(common, assignment_id=assignment, rule_version=rule["rule_version"],
                                                  schedule_code="TABLE21", mapping_status="DRAFT_SYNTHETIC",
                                                  mapping_note=f"Synthetic user-declared preparation {prep_id}; source record {ordinal}; not human-reviewed."))
        lineage.append({"source_record_ordinal": ordinal, "generated_record_ordinals": {name: ordinal for name in HEADERS},
                        "source_completion_value": values["visit_status"], "generated_completion_value": generated["visits.csv"][-1]["visit_status"]})
    uploads = {}
    for name, rows in generated.items():
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=HEADERS[name], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        encoded = stream.getvalue().encode("utf-8")
        parse_table(encoded, name, name)  # Preserve existing per-table bounds.
        uploads[name] = (name, encoded)
    manifest = {**spec, "preparation_id": prep_id, "source_display_name": sheet["display_name"], "source_bytes": len(raw),
                "source_record_count": len(sheet["records"]), "unmapped_columns": [c for c in sheet["headers"] if c not in mapping.values()],
                "generated_files": {name: {"sha256": hashlib.sha256(v[1]).hexdigest(), "records": len(generated[name])} for name, v in uploads.items()},
                "lineage": lineage, "declared_constants": {"anchor_code": rule["anchor_code"], "anchor_kind": rule["anchor_kind"],
                "visit_code": rule["supported_visit_code"], "event_kind": rule["event_kind"], "rule_version": rule["rule_version"],
                "schedule_code": "TABLE21", "mapping_status": "DRAFT_SYNTHETIC"},
                "derived_fields": {"assignment_id": "PREP- plus logical source row ordinal", "mapping_note": "Preparation ID and source ordinal"},
                "limitations": ["Column meanings and rule applicability are user declarations, not independently verified facts.",
                "One row must contain a recorded safety call and its actual vaccination reference; no cross-row joining.",
                "No rows are dropped, dates parsed/coerced, identifiers trimmed, or duplicate references collapsed.",
                "Repeated vaccination identifiers remain duplicate-key queries; repeating/longitudinal exports need a separately validated adapter.",
                "Original source.csv and this manifest must accompany evidence.json to inspect upstream evidence.",
                "Not a certified REDCap, OpenClinica or CDISC import. Synthetic data only; no clinical validation."]}
    return {"uploads": uploads, "manifest": manifest, "sheet": sheet, "source_bytes": raw}


def evidence_package(prepared, rule, rule_sha256, *, source_metadata=None):
    """Calculate through the unchanged adapter and archive the complete derivation chain."""
    if prepared["manifest"]["rule_sha256"] != rule_sha256:
        raise InputError("PREPARATION_RULE_CHANGED", "Prepare again with the current rule")
    bundle, encoded = check_uploads(prepared["uploads"], rule, rule_sha256, draft_confirmed=True, source_metadata=source_metadata)
    manifest = {**prepared["manifest"], "report_sha256": hashlib.sha256(encoded).hexdigest(), "run_id": bundle["run_id"]}
    files = {"source.csv": prepared["source_bytes"], "preparation.json": json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"),
             "evidence.json": encoded, **{name: value[1] for name, value in prepared["uploads"].items()},
             "README.txt": b"SYNTHETIC DRAFT ONLY. evidence.json describes generated CSV inputs. See preparation.json for column choices, declared constants and source.csv for exact original bytes. Raw source/generated CSV cells are unescaped machine inputs; do not treat them as spreadsheet-safe review lists. Hashes identify bytes, not truth or clinical approval.\n"}
    if sum(len(v) for v in files.values()) > MAX_PACKAGE_BYTES:
        raise InputError("PACKAGE_SIZE_LIMIT", "Complete evidence package exceeds 5,000,000 uncompressed bytes; no files were omitted")
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o600 << 16
            archive.writestr(item, value)
    return bundle, encoded, stream.getvalue()
