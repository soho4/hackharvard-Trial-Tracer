"""Identity and relationship checks, without date-window calculations."""

from collections import defaultdict
from datetime import date
import re

KEYS = {"anchors.csv": "anchor_id", "visits.csv": "visit_id", "assignments.csv": "assignment_id"}
SUPPORTED = {
    "anchors.csv": {"anchor_code": "OL_D1", "anchor_kind": "ACTUAL_VACCINATION"},
    "visits.csv": {"visit_code": "OL_D8", "event_kind": "SAFETY_PHONE_CALL"},
    "assignments.csv": {"rule_version": "A10_DRAFT_2", "schedule_code": "TABLE21"},
}


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("Date must have YYYY-MM-DD shape")
    return date.fromisoformat(value)


def evidence(table, record):
    return {"source_file": table["name"], "sha256": table["sha256"], **record}


def inspect_inputs(tables):
    """Return per-row issues, complete source accounting and indexed visit joins."""
    issues, indexes, by_id, accounting = {}, {}, {}, {}
    for name, table in tables.items():
        index, ids = defaultdict(list), defaultdict(list)
        for rec in table["records"]:
            row = rec["raw_record"]
            index[(row["study_id"], row[KEYS[name]])].append(rec)
            ids[row[KEYS[name]]].append(rec)
        indexes[name], by_id[name] = index, ids
        accounting[name] = {"record_count": len(table["records"]), "issues": []}
        for rec in table["records"]:
            row, ordinal = rec["raw_record"], rec["record_ordinal"]
            found = []

            def add(code, status, field=None):
                item = {"code": code, "status": status, "record_ordinal": ordinal}
                if field:
                    item["field"] = field
                found.append(item)

            for field, value in row.items():
                if field.endswith("_id") and (not value or value != value.strip()):
                    add("INVALID_ID", "DATA_QUERY", field)
            if len(index[(row["study_id"], row[KEYS[name]])]) > 1:
                add("DUPLICATE_KEY", "DATA_QUERY", KEYS[name])
            if row["study_id"] != "NCT04470427":
                add("UNSUPPORTED_STUDY", "NOT_EVALUABLE", "study_id")
            for field, expected in SUPPORTED[name].items():
                if row[field] != expected:
                    add("UNSUPPORTED_" + field.upper(), "NOT_EVALUABLE", field)
            for field in ("anchor_date", "actual_date"):
                if field in row:
                    try:
                        parse_date(row[field])
                    except ValueError:
                        add("INVALID_DATE", "DATA_QUERY", field)
            if name == "visits.csv" and row["visit_status"] != "COMPLETED":
                add("COMPLETION_UNKNOWN", "DATA_QUERY", "visit_status")
            if name == "assignments.csv":
                if row["mapping_status"] != "DRAFT_SYNTHETIC":
                    add("MAPPING_NOT_DRAFT_APPROVED", "NOT_EVALUABLE", "mapping_status")
                if not row["mapping_note"].strip():
                    add("MISSING_MAPPING_NOTE", "DATA_QUERY", "mapping_note")
            issues[(name, ordinal)] = found
            accounting[name]["issues"].extend({**item, "evidence": evidence(table, rec)} for item in found)

    visits, referenced = [], {name: set() for name in tables}
    for visit in tables["visits.csv"]["records"]:
        row, ordinal = visit["raw_record"], visit["record_ordinal"]
        problems = list(issues[("visits.csv", ordinal)])
        # Own row first; duplicate visit rows remain inspectable as conflicts.
        ev = [evidence(tables["visits.csv"], visit)]
        for duplicate in indexes["visits.csv"][(row["study_id"], row["visit_id"])]:
            if duplicate["record_ordinal"] != ordinal:
                ev.append(evidence(tables["visits.csv"], duplicate))
        joined = {}
        for name, key in (("anchors.csv", "anchor_id"), ("assignments.csv", "assignment_id")):
            matches = indexes[name].get((row["study_id"], row[key]), [])
            # A same-id row in a different study is conflicting evidence, never a valid join.
            candidates = matches or by_id[name].get(row[key], [])
            relation_issues = []
            if not candidates:
                relation_issues.append({"code": "MISSING_" + key.upper(), "status": "DATA_QUERY", "field": key})
            if len(matches) > 1:
                relation_issues.append({"code": "AMBIGUOUS_" + key.upper(), "status": "DATA_QUERY", "field": key})
            for rec in candidates:
                referenced[name].add(rec["record_ordinal"])
                ev.append(evidence(tables[name], rec))
                problems.extend({**item, "source_file": name} for item in issues[(name, rec["record_ordinal"])])
                for field in ("study_id", "participant_id", "site_id"):
                    if rec["raw_record"][field] != row[field]:
                        relation_issues.append({"code": "MISMATCH_" + field.upper(), "status": "DATA_QUERY", "field": field, "source_file": name, "related_record_ordinal": rec["record_ordinal"]})
            for item in relation_issues:
                problems.append(item)
                accounting["visits.csv"]["issues"].append({**item, "record_ordinal": ordinal, "evidence": evidence(tables["visits.csv"], visit)})
            joined[name] = matches[0] if len(matches) == 1 else None
        visits.append({"record": visit, "problems": problems, "evidence": ev, "joined": joined})
    for name, table in tables.items():
        accounting[name]["referenced_record_count"] = len(referenced[name]) if name != "visits.csv" else len(table["records"])
        accounting[name]["unreferenced_record_ordinals"] = [r["record_ordinal"] for r in table["records"] if name != "visits.csv" and r["record_ordinal"] not in referenced[name]]
    return {"input_accounting": accounting, "visits": visits}
