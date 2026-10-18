#!/usr/bin/env python3
"""Independent synthetic challenge: literal answers, real files, real CLI."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
HEADERS = {
    "anchors.csv": "study_id,participant_id,site_id,anchor_id,anchor_code,anchor_kind,anchor_date".split(","),
    "visits.csv": "study_id,participant_id,site_id,visit_id,visit_code,event_kind,actual_date,visit_status,anchor_id,assignment_id".split(","),
    "assignments.csv": "assignment_id,study_id,participant_id,site_id,rule_version,schedule_code,mapping_status,mapping_note".split(","),
}

# Calendar answers authored independently before running the application. A century
# divisible by 100 is not leap unless divisible by 400. No engine builds this oracle.
HAND_CASES = [
    ("minimum-year", "0001-01-01", "0001-01-08", "0001-01-08", "0001-01-11", 0),
    ("nineteenth-century", "1899-12-25", "1900-01-01", "1900-01-01", "1900-01-04", 0),
    ("1900-not-leap", "1900-02-22", "1900-03-01", "1900-03-01", "1900-03-04", 0),
    ("1900-one-early", "1900-02-22", "1900-02-28", "1900-03-01", "1900-03-04", 1),
    ("millennium", "1999-12-25", "2000-01-05", "2000-01-01", "2000-01-04", 1),
    ("2000-is-leap", "2000-02-22", "2000-02-29", "2000-02-29", "2000-03-03", 0),
    ("2000-upper-bound", "2000-02-22", "2000-03-03", "2000-02-29", "2000-03-03", 0),
    ("2000-two-late", "2000-02-22", "2000-03-05", "2000-02-29", "2000-03-03", 2),
    ("2024-leap-crossing", "2024-02-23", "2024-03-04", "2024-03-01", "2024-03-04", 0),
    ("2024-before-leap", "2024-02-20", "2024-02-26", "2024-02-27", "2024-03-01", 1),
    ("april-month-boundary", "2047-04-26", "2047-05-06", "2047-05-03", "2047-05-06", 0),
    ("2100-not-leap", "2100-02-22", "2100-03-05", "2100-03-01", "2100-03-04", 1),
    ("2400-is-leap", "2400-02-22", "2400-02-29", "2400-02-29", "2400-03-03", 0),
    ("maximum-year-safe", "9999-12-21", "9999-12-31", "9999-12-28", "9999-12-31", 0),
]


def authored_dataset():
    records = {name: [] for name in HEADERS}
    expected = []

    def add(tag, anchor_date, actual_date):
        identifier = "g3-synthetic-" + tag
        common = {"study_id": "NCT04470427", "participant_id": identifier + "-Δ", "site_id": "g3-synthetic-site-東京"}
        anchor = dict(common, anchor_id=identifier + "-anchor", anchor_code="OL_D1", anchor_kind="ACTUAL_VACCINATION", anchor_date=anchor_date)
        visit = dict(common, visit_id=identifier + "-visit", visit_code="OL_D8", event_kind="SAFETY_PHONE_CALL", actual_date=actual_date, visit_status="COMPLETED", anchor_id=anchor["anchor_id"], assignment_id=identifier + "-mapping")
        assignment = dict(common, assignment_id=visit["assignment_id"], rule_version="A10_DRAFT_2", schedule_code="TABLE21", mapping_status="DRAFT_SYNTHETIC", mapping_note='Independent authored synthetic record, not human review.\r\nQuoted "cell"; literal <script>alert("no execution")</script> 🧪')
        for name, row in (("anchors.csv", anchor), ("visits.csv", visit), ("assignments.csv", assignment)):
            records[name].append(row)
        return anchor, visit, assignment

    for tag, anchor_date, actual, target, latest, outside in HAND_CASES:
        _, visit, _ = add(tag, anchor_date, actual)
        expected.append({"visit_id": visit["visit_id"], "status": "PASS" if outside == 0 else "POTENTIAL_DEVIATION", "calculation": {"target": target, "earliest": target, "latest": latest, "actual": actual, "days_outside": outside}})

    uncertainties = [
        ("missing-anchor", "DATA_QUERY"), ("wrong-person", "DATA_QUERY"),
        ("unresolved-scope", "NOT_EVALUABLE"), ("unknown-completion", "DATA_QUERY"),
        ("duplicate-anchor", "DATA_QUERY"), ("decision-anchor", "NOT_EVALUABLE"),
        ("wrong-event", "NOT_EVALUABLE"), ("derived-overflow", "DATA_QUERY"),
        ("invalid-nonleap-date", "DATA_QUERY"), ("case-sensitive-id", "DATA_QUERY"),
    ]
    for tag, status in uncertainties:
        anchor, visit, assignment = add(tag, "2077-08-24", "2077-08-31")
        if tag == "missing-anchor":
            records["anchors.csv"].remove(anchor)
        elif tag == "wrong-person":
            anchor["participant_id"] = "another-synthetic-person"
        elif tag == "unresolved-scope":
            assignment["mapping_status"] = "UNRESOLVED"
        elif tag == "unknown-completion":
            visit["visit_status"] = "UNKNOWN"
        elif tag == "duplicate-anchor":
            records["anchors.csv"].append(dict(anchor))
        elif tag == "decision-anchor":
            anchor["anchor_kind"] = "PARTICIPANT_DECISION"
        elif tag == "wrong-event":
            visit["event_kind"] = "CLINIC_VISIT"
        elif tag == "derived-overflow":
            anchor["anchor_date"] = "9999-12-22"
        elif tag == "invalid-nonleap-date":
            visit["actual_date"] = "2100-02-29"
        elif tag == "case-sensitive-id":
            visit["anchor_id"] = visit["anchor_id"].upper()
        expected.append({"visit_id": visit["visit_id"], "status": status, "calculation": None})
    records["anchors.csv"].append(dict(records["anchors.csv"][0], anchor_id="g3-orphan-invalid-anchor", anchor_date="not-a-date"))
    records["assignments.csv"].append(dict(records["assignments.csv"][0], assignment_id="g3-orphan-invalid-mapping", participant_id=" "))
    return records, expected


def write_dataset(directory, records, *, newline="\r\n", bom=True):
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    for index, (name, fields) in enumerate(HEADERS.items()):
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(reversed(fields)), lineterminator=newline)
        writer.writeheader()
        writer.writerows(records[name])
        path = directory / f"unfamiliar-upload-{index + 31}.csv"
        path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + stream.getvalue().encode("utf-8"))
        paths[name] = path
    return paths


def cli_run(paths, output):
    command = [sys.executable, "-m", "trialtrace.cli"]
    for role in ("anchors", "visits", "assignments"):
        command.extend(["--" + role, str(paths[role + ".csv"])])
    command.extend(["--rule", str(ROOT / "rules/candidate_rule.json"), "--draft-synthetic", "--output", str(output)])
    return subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), capture_output=True, text=True, timeout=30)


def assert_report(bundle, paths, records, expected):
    actual = [{key: item[key] for key in ("visit_id", "status", "calculation")} for item in bundle["findings"]]
    assert actual == expected
    assert len({item["finding_id"] for item in bundle["findings"]}) == len(expected)
    assert bundle["clinical_validation"] is False
    assert bundle["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"
    assert bundle["run_mode"] == "DRAFT_ENGINEERING"
    assert bundle["summary"]["visit_evaluations"] == len(expected)
    assert bundle["summary"]["statuses"] == dict(Counter(item["status"] for item in expected))
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    assert {item["name"]: item["sha256"] for item in bundle["input_files"]} == hashes
    for name, rows in records.items():
        assert bundle["input_accounting"][name]["record_count"] == len(rows)
    for finding in bundle["findings"]:
        own = [item for item in finding["evidence"] if item["source_file"] == "visits.csv" and item["record_ordinal"] == finding["record_ordinal"]]
        assert len(own) == 1
        for evidence in finding["evidence"]:
            name, ordinal = evidence["source_file"], evidence["record_ordinal"]
            assert evidence["sha256"] == hashes[name]
            assert evidence["raw_record"] == records[name][ordinal - 1]
    for name in ("anchors.csv", "assignments.csv"):
        orphan = len(records[name])
        assert orphan in bundle["input_accounting"][name]["unreferenced_record_ordinals"]
        assert any(issue["record_ordinal"] == orphan for issue in bundle["input_accounting"][name]["issues"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    records, expected = authored_dataset()
    paths = write_dataset(args.out / "inputs", records)
    (args.out / "independently_authored_expected.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    output = args.out / "actual_bundle.json"
    execution = cli_run(paths, output)
    (args.out / "cli.stdout.log").write_text(execution.stdout, encoding="utf-8")
    (args.out / "cli.stderr.log").write_text(execution.stderr, encoding="utf-8")
    assert execution.returncode == 0, execution.stderr
    bundle = json.loads(output.read_bytes())
    assert_report(bundle, paths, records, expected)
    first = output.read_bytes()
    repeated = cli_run(paths, output)
    assert repeated.returncode == 0, repeated.stderr
    assert output.read_bytes() == first
    report = {
        "status": "PASS", "completed_at": datetime.now(timezone.utc).isoformat(),
        "basis": "Independent synthetic engineering challenge. Literal calendar expectations; no human or clinical source review.",
        "execution": "Real current-source CLI subprocess, using actual novel UTF-8 BOM/CRLF/reordered-header CSV files.",
        "visits": len(expected), "status_counts": dict(Counter(item["status"] for item in expected)),
        "checks": ["14 literal calendar cases including century leap rules and representable bounds", "10 uncertainty/relationship cases", "All source rows and orphan issues accounted", "Every evidence row and SHA matches actual input bytes", "Byte-identical repeated output"],
        "cli_command": execution.args, "cli_exit_code": execution.returncode,
        "input_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()},
        "rule_sha256": bundle["ruleset"]["sha256"], "code_sha256": bundle["producer"]["code_sha256"],
        "output_sha256": hashlib.sha256(first).hexdigest(), "run_id": bundle["run_id"],
    }
    (args.out / "challenge_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
