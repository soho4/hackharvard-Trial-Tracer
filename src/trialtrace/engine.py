"""Pure calendar arithmetic and conservative draft evaluation; no clinical approval."""

import hashlib
import json
from datetime import timedelta

from .errors import InputError
from .relationships import inspect_inputs, parse_date

RULE_FIELDS = {
    "schema_version", "rule_id", "rule_version", "source_id", "source_url", "source_locator",
    "study_id", "protocol_id", "amendment", "document_date", "scope", "supported_visit_code",
    "event_kind", "anchor_code", "anchor_kind", "offset_days", "lower_days", "upper_days",
    "bounds", "units", "interpretation_notes", "review_status", "data_kind", "clinical_validation",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def validate_offsets(offset_days, lower_days, upper_days):
    if any(type(v) is not int for v in (offset_days, lower_days, upper_days)):
        raise InputError("RULE_INTEGER", "Offsets and tolerances must be integers, never booleans")
    if offset_days < 0 or lower_days > 0 or upper_days < 0 or lower_days > upper_days:
        raise InputError("RULE_RANGE", "Offsets/tolerances violate the supported bounds policy")


def validate_rule(rule):
    try:
        canonical(rule)
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise InputError("RULE_ENCODING", "Rule must contain finite, UTF-8 encodable JSON values") from exc
    if not isinstance(rule, dict) or set(rule) != RULE_FIELDS:
        raise InputError("RULE_FIELDS", "Rule has missing or unknown fields/policy")
    validate_offsets(rule["offset_days"], rule["lower_days"], rule["upper_days"])
    required_values = {
        "schema_version": "trialtrace.rulecard.v0.3", "rule_id": "TABLE21_OL_D8_WINDOW",
        "rule_version": "A10_DRAFT_2", "study_id": "NCT04470427", "protocol_id": "mRNA-1273-P301",
        "supported_visit_code": "OL_D8", "event_kind": "SAFETY_PHONE_CALL", "anchor_code": "OL_D1",
        "anchor_kind": "ACTUAL_VACCINATION", "bounds": "inclusive", "units": "calendar_days",
        "review_status": "PENDING_TEAM_SOURCE_REVIEW", "data_kind": "SYNTHETIC_ONLY",
    }
    for field, expected in required_values.items():
        if rule[field] != expected:
            raise InputError("RULE_UNSUPPORTED", "Unsupported rule " + field, field=field)
    if rule["clinical_validation"] is not False or type(rule["amendment"]) is not int or rule["amendment"] != 10:
        raise InputError("RULE_IDENTITY", "Invalid clinical/source identity")
    for field in ("source_id", "source_url", "scope"):
        if not isinstance(rule[field], str) or not rule[field].strip():
            raise InputError("RULE_METADATA", "Missing rule metadata", field=field)
    if rule["source_url"] != "https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf":
        raise InputError("RULE_SOURCE", "Only the pinned protocol URL is supported")
    try:
        parse_date(rule["document_date"])
    except ValueError as exc:
        raise InputError("RULE_DATE", "Invalid source document date") from exc
    locator = rule["source_locator"]
    if not isinstance(locator, dict) or set(locator) != {"table", "printed_pages", "pdf_pages_one_indexed"}:
        raise InputError("RULE_LOCATOR", "Invalid source locator")
    if not isinstance(locator["table"], str) or not locator["table"].strip():
        raise InputError("RULE_LOCATOR", "Missing source table")
    for key in ("printed_pages", "pdf_pages_one_indexed"):
        if not isinstance(locator[key], list) or not locator[key] or any(type(p) is not int or p < 1 for p in locator[key]):
            raise InputError("RULE_LOCATOR", "Source pages must be positive integers")
    if not isinstance(rule["interpretation_notes"], list) or not rule["interpretation_notes"] or any(not isinstance(v, str) or not v.strip() for v in rule["interpretation_notes"]):
        raise InputError("RULE_NOTES", "Missing interpretation limitations")


def calculate(anchor_date, actual_date, offset_days=7, lower_days=0, upper_days=3):
    validate_offsets(offset_days, lower_days, upper_days)
    anchor, actual = parse_date(anchor_date), parse_date(actual_date)
    target = anchor + timedelta(days=offset_days)
    earliest = target + timedelta(days=lower_days)
    latest = target + timedelta(days=upper_days)
    outside = max((earliest - actual).days, (actual - latest).days, 0)
    return {"target": target.isoformat(), "earliest": earliest.isoformat(), "latest": latest.isoformat(), "actual": actual.isoformat(), "days_outside": outside}


def evaluate(tables, rule, rule_sha256, *, mode):
    validate_rule(rule)
    if mode != "DRAFT_ENGINEERING":
        raise InputError("SOURCE_REVIEW_REQUIRED", "Reviewed execution is blocked pending real source review and integrator acceptance; explicitly select draft engineering")
    inspected = inspect_inputs(tables, max_evidence_bytes=2_000_000)
    snapshot = hashlib.sha256(canonical([(n, t["sha256"]) for n, t in sorted(tables.items())])).hexdigest()
    findings = []
    for item in inspected["visits"]:
        rec, problems = item["record"], list(item["problems"])
        row, calculation = rec["raw_record"], None
        if not problems:
            try:
                calculation = calculate(item["joined"]["anchors.csv"]["raw_record"]["anchor_date"], row["actual_date"], rule["offset_days"], rule["lower_days"], rule["upper_days"])
            except OverflowError:
                problems.append({"code": "DERIVED_DATE_OVERFLOW", "status": "DATA_QUERY"})
        if any(p["status"] == "DATA_QUERY" for p in problems):
            status = "DATA_QUERY"
        elif problems:
            status = "NOT_EVALUABLE"
        else:
            status = "PASS" if calculation["days_outside"] == 0 else "POTENTIAL_DEVIATION"
        codes = list(dict.fromkeys(p["code"] for p in problems)) or ["WITHIN_INCLUSIVE_WINDOW" if status == "PASS" else "OUTSIDE_INCLUSIVE_WINDOW"]
        identity = ["trialtrace.finding.v1", snapshot, rule_sha256, mode, rec["record_ordinal"]]
        findings.append({
            "finding_id": hashlib.sha256(canonical(identity)).hexdigest(),
            "record_ordinal": rec["record_ordinal"],
            **{key: row[key] or None for key in ("participant_id", "site_id", "visit_id", "visit_code")},
            "study_id": row["study_id"] or None,
            "status": status, "reason": "; ".join(codes), "reason_codes": codes,
            "issues": problems, "calculation": calculation, "evidence": item["evidence"],
        })
    return {"findings": findings, "input_accounting": inspected["input_accounting"], "input_snapshot_sha256": snapshot,
            "summary": {"visit_evaluations": len(findings), "statuses": {s: sum(f["status"] == s for f in findings) for s in ("PASS", "POTENTIAL_DEVIATION", "DATA_QUERY", "NOT_EVALUABLE")}}}
