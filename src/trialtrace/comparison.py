"""Read and compare saved synthetic evidence reports without changing either one.

Public API:
    load_report(raw: bytes) -> dict
        Accept UTF-8 (optional leading BOM), at most 2,000,000 bytes, depth <=64.
        Reject duplicate JSON keys, non-finite numbers, invalid Unicode, schema
        failures, and semantic inconsistencies with structured ``InputError``.
    compare_reports(before: dict, after: dict) -> dict
        Validate and copy both bounded JSON objects. Pair only identities that
        are unique on both sides: exact study/participant/site/visit strings.
        Own visit evidence can supply absent/null fields; conflicting, blank,
        whitespace-padded, or duplicate identities remain explicitly unmatched.
        Duplicate canonical (study_id, visit_id) keys make every associated row
        ambiguous even when participant or site values differ.
    validate_report(bundle: dict) -> None
        Apply the same bounded JSON, schema, and semantic checks to an already
        decoded object, without modifying it. Raises structured InputError.

The comparison has schema_version ``trialtrace.comparison.v1``, before/after
run references, context_changes, summary, matched, unmatched_before/after,
ambiguous_groups, and limitations. Each matched item has identity, both source
finding IDs/ordinals, change_kind, changed_fields, and changes mapping a field
to {before, after}. ``changed`` counts status/calculation/reason/visit-code/raw
row changes. ``provenance_only`` separates file hashes, raw CSV formatting, and
record positions. ``added``/``removed`` count unique usable identities present
on only one side; these are report records, never inferred new/missed events.

All matching work is linear in the bounded report content, apart from sorting
evidence projections for order-independent comparison. No arithmetic is rerun,
source authenticity established, or improvement/clinical conclusion assigned.
"""

from collections import Counter, defaultdict
import json
import math

from .errors import InputError
from .exporter import MAX_OUTPUT_BYTES, validate_bundle


MAX_DEPTH = 64
IDENTITY_FIELDS = ("study_id", "participant_id", "site_id", "visit_id")
OUTCOMES = ("PASS", "POTENTIAL_DEVIATION", "DATA_QUERY", "NOT_EVALUABLE")
CONTEXT_FIELDS = ("ruleset", "source", "run_mode", "review_status", "producer", "schema_version", "data_kind", "clinical_validation", "input_files", "limitations")
RESULT_FIELDS = ("status", "calculation", "reason", "reason_codes", "visit_code")


def _check_json_tree(value):
    """Bound nesting and reject values JSON cannot represent safely."""
    def members(mapping):
        for key, child in mapping.items():
            if not isinstance(key, str):
                raise InputError("REPORT_JSON", "Saved report object keys must be strings")
            yield key
            yield child

    pending, size_floor = [(iter((value,)), 0)], 0
    while pending:
        iterator, depth = pending[-1]
        try:
            item = next(iterator)
        except StopIteration:
            pending.pop()
            continue
        if depth > MAX_DEPTH:
            raise InputError("REPORT_DEPTH", "Saved report nesting exceeds 64 levels")
        if isinstance(item, str):
            if len(item) > MAX_OUTPUT_BYTES:
                raise InputError("REPORT_SIZE_LIMIT", "Saved report exceeds the 2,000,000-byte limit")
            try:
                item.encode("utf-8")
            except UnicodeError as exc:
                raise InputError("REPORT_UNICODE", "Saved report contains invalid Unicode") from exc
            size_floor += len(item) + 2
        elif type(item) is dict:
            size_floor += 2 + len(item)
            pending.append((members(item), depth + 1))
        elif type(item) is list:
            size_floor += 2 + max(len(item) - 1, 0)
            pending.append((iter(item), depth + 1))
        elif type(item) is float:
            if not math.isfinite(item):
                raise InputError("REPORT_JSON", "Saved report numbers must be finite")
            size_floor += 1
        elif item is not None and type(item) not in (bool, int):
            raise InputError("REPORT_JSON", "Saved report contains a non-JSON value")
        else:
            size_floor += 1
        if size_floor > MAX_OUTPUT_BYTES:
            raise InputError("REPORT_SIZE_LIMIT", "Saved report exceeds the 2,000,000-byte limit")


def _optional_metadata(bundle):
    """Validate known extension structures before the shared semantic validator."""
    # Local import: inspection's worklists call validate_report, while this
    # standalone accounting helper never imports comparison itself.
    from .inspection import validate_input_accounting
    validate_input_accounting(bundle)
    if "summary" in bundle:
        summary = bundle["summary"]
        if not isinstance(summary, dict):
            raise InputError("REPORT_SUMMARY", "Report summary must be an object")
        findings = bundle.get("findings")
        if isinstance(findings, list):
            if "visit_evaluations" in summary and (type(summary["visit_evaluations"]) is not int or summary["visit_evaluations"] != len(findings)):
                raise InputError("REPORT_SUMMARY", "Evaluation count disagrees with the finding count")
            if "statuses" in summary:
                statuses = summary["statuses"]
                observed = Counter(item.get("status") for item in findings if isinstance(item, dict) and isinstance(item.get("status"), str))
                if not isinstance(statuses, dict) or set(statuses) != set(OUTCOMES) or any(type(statuses[status]) is not int or statuses[status] != observed[status] for status in OUTCOMES):
                    raise InputError("REPORT_SUMMARY", "Outcome counts disagree with the findings")


def _validate(bundle):
    if not isinstance(bundle, dict):
        raise InputError("REPORT_STRUCTURE", "A saved evidence report must be a JSON object")
    try:
        _optional_metadata(bundle)
        validate_bundle(bundle)
    except InputError:
        raise
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, RecursionError, UnicodeError) as exc:
        raise InputError("REPORT_STRUCTURE", "Saved report contains malformed structured fields") from exc


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("REPORT_DUPLICATE_KEY", "Saved report contains a duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(_value):
    raise InputError("REPORT_JSON", "Saved report numbers must be finite")


def load_report(raw):
    """Return a validated saved bundle from bounded UTF-8 bytes; see module API."""
    if not isinstance(raw, (bytes, bytearray)):
        raise InputError("REPORT_BYTES", "Provide saved report bytes")
    if len(raw) > MAX_OUTPUT_BYTES:
        raise InputError("REPORT_SIZE_LIMIT", "Saved report exceeds the 2,000,000-byte limit")
    try:
        bundle = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except InputError:
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InputError("REPORT_JSON", "Saved report is not valid bounded UTF-8 JSON") from exc
    _check_json_tree(bundle)
    _validate(bundle)
    return bundle


def _validated_copy(bundle):
    _check_json_tree(bundle)
    output = bytearray()
    try:
        encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        for chunk in encoder.iterencode(bundle):
            encoded = chunk.encode("utf-8")
            if len(output) + len(encoded) > MAX_OUTPUT_BYTES:
                raise InputError("REPORT_SIZE_LIMIT", "Saved report exceeds the 2,000,000-byte limit")
            output.extend(encoded)
    except InputError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError) as exc:
        raise InputError("REPORT_JSON", "Saved report is not valid bounded JSON") from exc
    return load_report(bytes(output))


def validate_report(bundle):
    """Validate a bounded decoded report without changing it; return None."""
    _validated_copy(bundle)
    return None


def _identity(finding, fields=IDENTITY_FIELDS):
    # Match the finding's own logical visit row, not an anchor/assignment belonging
    # to somebody else. Legacy source filenames are permitted by the contract.
    candidates = [item["raw_record"] for item in finding["evidence"] if item["record_ordinal"] == finding["record_ordinal"] and "visit_id" in item["raw_record"]]
    if len(candidates) > 1:
        return None, "CONFLICTING_VISIT_EVIDENCE"
    own = candidates[0] if candidates else {}
    identity = {}
    for field in fields:
        declared, recorded = finding.get(field), own.get(field)
        for value in (declared, recorded):
            if value is not None and (not isinstance(value, str) or not value or value != value.strip()):
                return None, "MISSING_OR_INVALID_IDENTITY"
        if declared is not None and recorded is not None and declared != recorded:
            return None, "CONFLICTING_IDENTITY"
        value = declared if declared is not None else recorded
        if value is None:
            return None, "MISSING_OR_INVALID_IDENTITY"
        identity[field] = value
    return tuple(identity[field] for field in fields), None


def _reference(finding, identity, reason):
    return {"finding_id": finding["finding_id"], "record_ordinal": finding["record_ordinal"], "identity": None if identity is None else dict(zip(IDENTITY_FIELDS, identity)), "reason": reason}


def _evidence_projection(finding, *, provenance):
    if provenance:
        fields = ("source_file", "record_ordinal", "sha256", "raw_csv")
    else:
        fields = ("source_file", "raw_record")
    projected = [{field: item.get(field) for field in fields} for item in finding["evidence"]]
    return sorted(projected, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def compare_reports(before, after):
    """Return a neutral, JSON-safe comparison; neither supplied report is mutated."""
    before, after = _validated_copy(before), _validated_copy(after)
    indexes, identities, visit_indexes = [], [], []
    for report in (before, after):
        index, visit_index, found = defaultdict(list), defaultdict(list), []
        for finding in report["findings"]:
            identity, reason = _identity(finding)
            visit_key, _ = _identity(finding, ("study_id", "visit_id"))
            found.append((identity, reason, visit_key))
            if identity is not None:
                index[identity].append(finding)
            if visit_key is not None:
                visit_index[visit_key].append(finding)
        indexes.append(index)
        identities.append(found)
        visit_indexes.append(visit_index)
    before_index, after_index = indexes
    before_visits, after_visits = visit_indexes
    ambiguous = {key for index in visit_indexes for key, group in index.items() if len(group) > 1}
    result = {
        "schema_version": "trialtrace.comparison.v1", "clinical_validation": False,
        "before": {"run_id": before["run_id"], "finding_count": len(before["findings"])},
        "after": {"run_id": after["run_id"], "finding_count": len(after["findings"])},
        "context_changes": [{"field": field, "before": before.get(field), "after": after.get(field)} for field in CONTEXT_FIELDS if before.get(field) != after.get(field)],
        "summary": {key: 0 for key in ("matched", "changed", "provenance_only", "unchanged", "added", "removed", "unmatched_before", "unmatched_after")},
        "matched": [], "unmatched_before": [], "unmatched_after": [],
        "ambiguous_groups": [{"visit_key": dict(zip(("study_id", "visit_id"), key)), "before_finding_ids": [item["finding_id"] for item in before_visits.get(key, [])], "after_finding_ids": [item["finding_id"] for item in after_visits.get(key, [])]} for key in sorted(ambiguous)],
        "limitations": [
            "Comparison of saved synthetic report content only. No clinical validation, improvement judgment, or source approval is implied.",
            "Changed rule, source, execution mode, review status, or producer can affect comparability; inspect context changes before interpreting finding differences.",
            "Only unique exact study/participant/site/visit identities are paired. Duplicate study/visit keys are ambiguous even if owner/site differs. Missing and conflicting identities remain unmatched.",
            "Added and removed mean unique report identities present on one side; they do not prove new, missed, completed, or corrected activities.",
            "Declared hashes are checked for internal consistency; the original input files and protocol are not authenticated by comparing saved reports.",
        ],
    }
    for side, report, found, opposite in (("before", before, identities[0], after_index), ("after", after, identities[1], before_index)):
        for finding, (identity, reason, visit_key) in zip(report["findings"], found):
            if visit_key in ambiguous:
                reason = "DUPLICATE_IDENTITY"
            elif identity is not None and identity not in opposite:
                reason = "ONLY_" + side.upper()
                result["summary"]["removed" if side == "before" else "added"] += 1
            if reason is not None:
                result["unmatched_" + side].append(_reference(finding, identity, reason))
                continue
            if side == "after":
                continue
            paired = opposite[identity][0]
            changes = {field: {"before": finding.get(field), "after": paired.get(field)} for field in RESULT_FIELDS if finding.get(field) != paired.get(field)}
            for field, provenance in (("raw_evidence", False), ("evidence_provenance", True)):
                left, right = _evidence_projection(finding, provenance=provenance), _evidence_projection(paired, provenance=provenance)
                if left != right:
                    changes[field] = {"before": left, "after": right}
            substantive = set(changes) - {"evidence_provenance"}
            kind = "changed" if substantive else "provenance_only" if changes else "unchanged"
            result["matched"].append({"identity": dict(zip(IDENTITY_FIELDS, identity)), "before_finding_id": finding["finding_id"], "after_finding_id": paired["finding_id"], "before_record_ordinal": finding["record_ordinal"], "after_record_ordinal": paired["record_ordinal"], "change_kind": kind, "changed_fields": list(changes), "changes": changes})
            result["summary"][kind] += 1
    for name in ("matched", "unmatched_before", "unmatched_after"):
        result["summary"][name] = len(result[name])
    return result
