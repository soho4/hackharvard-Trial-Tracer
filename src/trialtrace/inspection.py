"""Read-only intake diagnostics and evidence-linked review lists, never adjudication."""

from collections import Counter
from collections.abc import Mapping
import csv
import hashlib
import io
import json
import re
import unicodedata

from .engine import validate_rule
from .errors import InputError
from .exporter import MAX_OUTPUT_BYTES
from .importer import HEADERS, MAX_BYTES, parse_table
from .relationships import inspect_inputs


def inspect_uploads(uploads, rule, rule_sha256):
    """Inspect every supplied table independently; do not calculate a timing result.

    Row-level problems remain inspectable and do not block a draft check from
    returning DATA_QUERY/NOT_EVALUABLE. Readiness is not source approval, and the
    eventual full export can still exceed its separate serialized-size limit.
    """
    result = {
        "ready_for_draft_check": False, "missing_roles": [], "unexpected_roles": [],
        "configuration_problems": [], "files": [], "input_accounting": None,
        "relationship_summary": None, "inspection_problems": [], "timing_evaluated": False,
    }
    try:
        validate_rule(rule)
    except InputError as error:
        result["configuration_problems"].append(error.diagnostic())
    if not isinstance(rule_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", rule_sha256):
        result["configuration_problems"].append(InputError("RULE_HASH", "Rule digest must be a lowercase SHA-256").diagnostic())
    if not isinstance(uploads, Mapping):
        result["inspection_problems"].append(InputError("INPUT_ROLES", "Uploads must map the three logical roles to file bytes").diagnostic())
        uploads = {}
    result["unexpected_roles"] = sorted(str(role) for role in uploads if role not in HEADERS)
    tables = {}
    for role in HEADERS:
        upload = uploads.get(role)
        item = {"role": role, "state": "MISSING", "display_name": None, "byte_count": None,
                "sha256": None, "bom": None, "record_count": None, "problems": []}
        result["files"].append(item)
        if upload is None:
            result["missing_roles"].append(role)
            continue
        item["state"] = "REJECTED"
        try:
            if not isinstance(upload, (tuple, list)) or len(upload) != 2:
                raise InputError("UPLOAD_SHAPE", "A file requires a display filename and exact bytes", file=role)
            display, raw = upload
            if not isinstance(display, str):
                raise InputError("UPLOAD_FILENAME", "Display filename must be text", file=role)
            item["display_name"] = "".join(c for c in display if c.isprintable())[:200] or role
            if not isinstance(raw, bytes):
                raise InputError("UPLOAD_BYTES", "Uploaded content must be bytes; no decoding or coercion is performed", file=role)
            item["byte_count"] = len(raw)
            item["bom"] = raw.startswith(b"\xef\xbb\xbf")
            # The parser rejects oversized bytes immediately; do not hash an
            # arbitrarily large object merely to describe a rejected upload.
            if len(raw) <= MAX_BYTES:
                item["sha256"] = hashlib.sha256(raw).hexdigest()
            table = parse_table(raw, role, display)
        except InputError as error:
            item["problems"].append(error.diagnostic())
            continue
        tables[role] = table
        item.update(state="PARSED", display_name=table["display_name"], record_count=len(table["records"]))
    if set(tables) == set(HEADERS):
        try:
            inspected = inspect_inputs(tables, max_evidence_bytes=MAX_OUTPUT_BYTES)
        except InputError as error:
            result["inspection_problems"].append(error.diagnostic())
        else:
            result["input_accounting"] = inspected["input_accounting"]
            visits = []
            counts = Counter()
            for joined in inspected["visits"]:
                record = joined["record"]
                counts.update(problem["code"] for problem in joined["problems"])
                visits.append({
                    "record_ordinal": record["record_ordinal"],
                    **{key: record["raw_record"][key] for key in ("participant_id", "site_id", "visit_id")},
                    "issues": [dict(problem) for problem in joined["problems"]],
                    "evidence_refs": [_evidence_ref(item) for item in joined["evidence"]],
                })
            result["relationship_summary"] = {
                "visit_records": len(visits),
                "visits_with_issues": sum(bool(visit["issues"]) for visit in visits),
                "issue_occurrences_by_code": dict(sorted(counts.items())),
                "visits": visits,
                "note": "Identity, relationship and scope checks only; timing was not evaluated.",
            }
    result["ready_for_draft_check"] = not any((
        result["missing_roles"], result["unexpected_roles"], result["configuration_problems"],
        result["inspection_problems"], any(item["state"] != "PARSED" for item in result["files"]),
    ))
    return result


def validate_input_accounting(bundle):
    """Validate optional accounting before consumers index it; absent means unknown.

    This helper validates accounting only and does not import comparison, avoiding
    a cycle with comparison.validate_report, which calls it before base validation.
    """
    def fail(path, message):
        raise InputError("ACCOUNTING_METADATA", message, path=path)

    if not isinstance(bundle, dict):
        fail("report", "Report must be an object")
    if "input_accounting" not in bundle:
        return None
    accounting = bundle["input_accounting"]
    if not isinstance(accounting, dict):
        fail("input_accounting", "Accounting must be an object when supplied")
    inputs = bundle.get("input_files")
    if not isinstance(inputs, list) or not inputs:
        fail("input_files", "Accounting requires declared input files")
    hashes = {}
    for index, item in enumerate(inputs):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            fail(f"input_files[{index}]", "Input file must have a nonempty name")
        if item["name"] in hashes or not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            fail(f"input_files[{index}]", "Input file names must be unique and hashes valid")
        hashes[item["name"]] = item["sha256"]
    if set(accounting) != set(hashes):
        fail("input_accounting", "Accounting must cover exactly the declared input files")
    for name, table in accounting.items():
        where = f"input_accounting.{name}"
        if not isinstance(table, dict):
            fail(where, "Table accounting must be an object")
        for key in ("record_count", "referenced_record_count"):
            if type(table.get(key)) is not int or table[key] < 0:
                fail(where + "." + key, "Record counts must be nonnegative integers")
        total, referenced = table["record_count"], table["referenced_record_count"]
        if referenced > total:
            fail(where, "Referenced count cannot exceed supplied record count")
        unused = table.get("unreferenced_record_ordinals")
        if not isinstance(unused, list) or any(type(value) is not int or not 1 <= value <= total for value in unused):
            fail(where + ".unreferenced_record_ordinals", "Unreferenced ordinals must be positive integers within the table")
        if len(set(unused)) != len(unused) or len(unused) != total - referenced:
            fail(where + ".unreferenced_record_ordinals", "Unreferenced ordinals must be unique and conserve record counts")
        if not isinstance(table.get("issues"), list):
            fail(where + ".issues", "Issues must be an array")
    for name, table in accounting.items():
        for index, issue in enumerate(table["issues"]):
            where = f"input_accounting.{name}.issues[{index}]"
            if not isinstance(issue, dict):
                fail(where, "Issue must be an object")
            if not isinstance(issue.get("code"), str) or not issue["code"]:
                fail(where + ".code", "Issue code must be a nonempty string")
            if issue.get("status") not in ("DATA_QUERY", "NOT_EVALUABLE"):
                fail(where + ".status", "Input issues must be DATA_QUERY or NOT_EVALUABLE")
            ordinal = issue.get("record_ordinal")
            if type(ordinal) is not int or not 1 <= ordinal <= table["record_count"]:
                fail(where + ".record_ordinal", "Issue ordinal must identify a supplied record")
            if "field" in issue and (not isinstance(issue["field"], str) or not issue["field"]):
                fail(where + ".field", "Issue field must be nonempty text")
            related = issue.get("source_file")
            if "source_file" in issue and (not isinstance(related, str) or related not in hashes):
                fail(where + ".source_file", "Related source must be a declared input file")
            if "related_record_ordinal" in issue:
                related_ordinal = issue["related_record_ordinal"]
                if related is None or type(related_ordinal) is not int or not 1 <= related_ordinal <= accounting[related]["record_count"]:
                    fail(where + ".related_record_ordinal", "Related ordinal must identify a record in the related source")
            evidence = issue.get("evidence")
            if not isinstance(evidence, dict):
                fail(where + ".evidence", "Issue requires its original evidence record")
            if evidence.get("source_file") != name or evidence.get("record_ordinal") != ordinal or type(evidence.get("record_ordinal")) is not int:
                fail(where + ".evidence", "Evidence must identify the issue's containing table and ordinal")
            if evidence.get("sha256") != hashes[name]:
                fail(where + ".evidence.sha256", "Evidence hash must match the declared input file")
            if not isinstance(evidence.get("raw_record"), dict):
                fail(where + ".evidence.raw_record", "Evidence must contain the original record object")
    # Accounting may omit details of unused valid records, but it must never
    # contradict a reference that is actually present in a finding. Do not infer
    # that an absent reference proves a record was unused in a legacy report.
    findings = bundle.get("findings")
    observed = {name: set() for name in accounting}
    unused = {name: set(table["unreferenced_record_ordinals"]) for name, table in accounting.items()}
    if isinstance(findings, list):
        for finding in findings:
            if not isinstance(finding, dict) or not isinstance(finding.get("evidence"), list):
                continue  # The full report validator checks the base structure.
            for evidence in finding["evidence"]:
                if not isinstance(evidence, dict):
                    continue
                name, ordinal = evidence.get("source_file"), evidence.get("record_ordinal")
                if not isinstance(name, str) or name not in accounting:
                    continue  # Unknown evidence roles fail base semantic checks.
                if type(ordinal) is not int or not 1 <= ordinal <= accounting[name]["record_count"]:
                    fail("input_accounting." + name, "Finding evidence ordinal exceeds the declared supplied records")
                if ordinal in unused[name]:
                    fail("input_accounting." + name, "A record cited in a finding cannot also be declared unreferenced")
                observed[name].add(ordinal)
        for name, ordinals in observed.items():
            if len(ordinals) > accounting[name]["referenced_record_count"]:
                fail("input_accounting." + name, "Referenced count cannot be smaller than observed distinct finding references")
    return accounting


_ACTIONS = {
    "INVALID_ID": "Verify the identifier against the original record; resolve blanks or accidental whitespace explicitly.",
    "DUPLICATE_KEY": "Resolve duplicate study/key records against the source; do not automatically choose one row.",
    "INVALID_DATE": "Verify the source date and supply a valid YYYY-MM-DD value only when supported; do not infer a missing date.",
    "COMPLETION_UNKNOWN": "Confirm documented event completion; a populated date alone does not establish completion.",
    "MISSING_ANCHOR_ID": "Verify the reference and supply its matching actual vaccination record; an absent reference does not prove a missed event.",
    "MISSING_ASSIGNMENT_ID": "Verify the reference and supply the matching synthetic scope assignment.",
    "AMBIGUOUS_ANCHOR_ID": "Resolve duplicate anchor keys and identity against the source before choosing a vaccination record.",
    "AMBIGUOUS_ASSIGNMENT_ID": "Resolve duplicate assignment keys and scope against the source before selecting a mapping.",
    "MAPPING_NOT_DRAFT_APPROVED": "Resolve synthetic applicability explicitly. Draft calculation requires DRAFT_SYNTHETIC with a note; a CSV label never establishes human review.",
    "MISSING_MAPPING_NOTE": "Document why this synthetic case uses the supported schedule; do not add an unperformed review claim.",
    "UNSUPPORTED_STUDY": "Check the study mapping. This check supports NCT04470427 only; other studies need their own supported rule.",
    "UNSUPPORTED_ANCHOR_CODE": "Verify that the mapped anchor is actual OL-D1 vaccination; do not substitute decision, consent or booking dates.",
    "UNSUPPORTED_ANCHOR_KIND": "Verify that the mapped anchor is actual OL-D1 vaccination; do not substitute decision, consent or booking dates.",
    "UNSUPPORTED_VISIT_CODE": "Verify whether this is the documented OL-D8 safety phone call; another event requires a supported explicit rule.",
    "UNSUPPORTED_EVENT_KIND": "Verify whether this is the documented OL-D8 safety phone call; another event requires a supported explicit rule.",
    "UNSUPPORTED_RULE_VERSION": "Check the explicit amendment and schedule mapping; do not infer applicability from a date alone.",
    "UNSUPPORTED_SCHEDULE_CODE": "Check the explicit amendment and schedule mapping; do not infer applicability from a date alone.",
    "DERIVED_DATE_OVERFLOW": "Verify source dates and configured range; the derived interval exceeds the supported calendar range and has no timing conclusion.",
    "OUTSIDE_INCLUSIVE_WINDOW": "Review the documented vaccination and call dates against the candidate window and source. This potential deviation is unconfirmed.",
    "WITHIN_INCLUSIVE_WINDOW": "No issue was found for this supported timing check; this does not establish overall compliance or safety.",
}
for _code in ("MISMATCH_STUDY_ID", "MISMATCH_PARTICIPANT_ID", "MISMATCH_SITE_ID"):
    _ACTIONS[_code] = "Verify cross-file study, participant and site identity before relating records; do not join across people, sites or studies."


def _suggestion(codes):
    generic = "Review the supplied reason and supporting records; resolve documented data or scope questions before drawing a conclusion."
    return " ".join(dict.fromkeys(_ACTIONS.get(code, generic) for code in codes))


def _evidence_ref(evidence):
    return {key: evidence[key] for key in ("source_file", "record_ordinal", "sha256")}


def _validate_report(bundle):
    # Local import keeps accounting validation reusable by comparison itself.
    from .comparison import validate_report
    validate_report(bundle)


def build_worklist(bundle, *, include_pass=False):
    """Return one row per actual finding selected for review; no mutable decisions."""
    _validate_report(bundle)
    rows = []
    for finding in bundle["findings"]:
        if finding["status"] == "PASS" and not include_pass:
            continue
        codes = finding.get("reason_codes", [finding["reason"]])
        if not isinstance(codes, list) or not codes or any(not isinstance(code, str) or not code for code in codes):
            raise InputError("WORKLIST_METADATA", "Finding reason_codes must be a nonempty array of text", finding_id=finding["finding_id"])
        rows.append({
            "run_id": bundle["run_id"],
            **{key: finding[key] for key in ("finding_id", "record_ordinal", "participant_id", "site_id", "visit_id", "visit_code", "status", "reason")},
            "reason_codes": list(codes), "suggested_action": _suggestion(codes),
            "evidence_refs": [_evidence_ref(evidence) for evidence in finding["evidence"]],
            "review_status": bundle["review_status"],
        })
    return rows


def build_input_issue_list(bundle):
    """Return one row per accounting issue, including issues on unreferenced rows."""
    _validate_report(bundle)
    accounting = validate_input_accounting(bundle)
    if accounting is None:
        return []
    rows = []
    for name in sorted(accounting):
        table = accounting[name]
        for index, issue in enumerate(table["issues"]):
            raw = issue["evidence"]["raw_record"]
            identities = {key: raw.get(key) for key in ("study_id", "participant_id", "site_id", "visit_id", "anchor_id", "assignment_id")}
            if any(value is not None and not isinstance(value, str) for value in identities.values()):
                raise InputError("ACCOUNTING_METADATA", "Accounting evidence identifiers must be text or null", source_file=name, record_ordinal=issue["record_ordinal"])
            identity = json.dumps(["trialtrace.input-issue.v1", bundle["run_id"], name, index], ensure_ascii=False, separators=(",", ":"))
            rows.append({
                "run_id": bundle["run_id"], "input_issue_id": hashlib.sha256(identity.encode()).hexdigest(),
                "source_file": name, "record_ordinal": issue["record_ordinal"],
                "code": issue["code"], "status": issue["status"], "field": issue.get("field"),
                **identities,
                "is_unreferenced": issue["record_ordinal"] in table["unreferenced_record_ordinals"],
                "related_source_file": issue.get("source_file"), "related_record_ordinal": issue.get("related_record_ordinal"),
                "suggested_action": _suggestion([issue["code"]]), "evidence_ref": _evidence_ref(issue["evidence"]),
                "review_status": bundle["review_status"],
            })
    return rows


_FINDING_COLUMNS = ("run_id", "finding_id", "record_ordinal", "participant_id", "site_id", "visit_id", "visit_code", "status", "reason", "reason_codes", "suggested_action", "evidence_refs", "review_status")
_ISSUE_COLUMNS = ("run_id", "input_issue_id", "source_file", "record_ordinal", "code", "status", "field", "study_id", "participant_id", "site_id", "visit_id", "anchor_id", "assignment_id", "is_unreferenced", "related_source_file", "related_record_ordinal", "suggested_action", "evidence_ref", "review_status")


def _csv_cell(value):
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if not isinstance(value, str):
        return value
    prefix_end = 0
    control_prefix = False
    for character in value:
        is_control = unicodedata.category(character).startswith("C")
        if not character.isspace() and not is_control:
            break
        control_prefix = control_prefix or is_control
        prefix_end += 1
    remainder = value[prefix_end:]
    if control_prefix or remainder[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def _csv(rows, columns):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\r\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_cell(row[key]) for key in columns})
    return stream.getvalue().encode("utf-8")


def worklist_csv(bundle, *, include_pass=False):
    """Spreadsheet-safe derived CSV; the canonical JSON is never modified."""
    return _csv(build_worklist(bundle, include_pass=include_pass), _FINDING_COLUMNS)


def input_issues_csv(bundle):
    """Separate issue-count export; multiple reasons for one record remain rows."""
    return _csv(build_input_issue_list(bundle), _ISSUE_COLUMNS)
