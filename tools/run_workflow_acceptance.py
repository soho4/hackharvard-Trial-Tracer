#!/usr/bin/env python3
"""Execute the literal, synthetic workflow challenge through installed code and CLI."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

from record_command import run_record
from trialtrace.cli import load_rule
from trialtrace.comparison import load_report, compare_reports
from trialtrace.exporter import code_digest
from trialtrace.inspection import inspect_uploads, build_worklist, worklist_csv, build_input_issue_list, input_issues_csv
from trialtrace.source import hash_source_pdf
from trialtrace.workflow import check_uploads

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-pdf", type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    expected_path = ROOT / "examples/workflows/expected.json"
    expected = json.loads(expected_path.read_bytes())
    rule, rule_hash = load_rule(ROOT / "rules/candidate_rule.json")
    source = hash_source_pdf(args.source_pdf) if args.source_pdf else None
    reports, results = {}, []
    for version in ("before", "after"):
        folder = ROOT / "examples/workflows" / version
        uploads = {role: (role, (folder / role).read_bytes()) for role in ("anchors.csv", "visits.csv", "assignments.csv")}
        intake = inspect_uploads(uploads, rule, rule_hash)
        assert intake["ready_for_draft_check"] and intake["timing_evaluated"] is False
        assert {item["role"]: item["record_count"] for item in intake["files"]} == {"anchors.csv": 5, "visits.csv": 6, "assignments.csv": 6}
        target = out / (version + ".json")
        command = [sys.executable, "-I", "-m", "trialtrace.cli", "--draft-synthetic"]
        for role in uploads:
            command += ["--" + role.removesuffix(".csv"), str(folder / role)]
        command += ["--rule", str(ROOT / "rules/candidate_rule.json"), "--output", str(target)]
        if args.source_pdf:
            command += ["--source-pdf", str(args.source_pdf.resolve())]
        record, record_folder = run_record(command, ROOT.parent, out / "commands", version + "-actual-installed-cli")
        assert record["exit_code"] == 0, record_folder
        raw = target.read_bytes()
        report = reports[version] = load_report(raw)
        assert report["summary"]["statuses"] == expected[version + "_statuses"]
        bundle, encoded = check_uploads(uploads, rule, rule_hash, draft_confirmed=True, source_metadata=source)
        assert encoded == raw and bundle == report
        queue = build_worklist(report)
        issues = build_input_issue_list(report)
        assert len(queue) == expected[version + "_review_findings"]
        assert len(issues) == expected["input_issue_count"]
        assert sum(row["is_unreferenced"] for row in issues) == expected["unreferenced_issues"]
        review_csv, issue_csv = worklist_csv(report), input_issues_csv(report)
        (out / (version + "-review.csv")).write_bytes(review_csv)
        (out / (version + "-input-issues.csv")).write_bytes(issue_csv)
        (out / (version + "-intake.json")).write_text(json.dumps(intake, indent=2, ensure_ascii=False) + "\n")
        if version == "after":
            parsed = list(csv.DictReader(io.StringIO(review_csv.decode("utf-8-sig"))))
            assert parsed[0]["participant_id"] == expected["csv_escape_expected"]
            assert report["findings"][0]["participant_id"] == expected["json_identity_unchanged"]
            assert report["findings"][0]["calculation"] == expected["changed_calculation"]
        results.append({"version": version, "counts": report["summary"]["statuses"], "review_findings": len(queue),
                        "input_issues": len(issues), "cli_adapter_bytes_equal": True, "bytes": len(raw), "sha256": sha(raw),
                        "inputs": {role: sha(value[1]) for role, value in uploads.items()}})
    comparison = compare_reports(reports["before"], reports["after"])
    assert comparison["summary"] == expected["comparison"]
    changed = [row for row in comparison["matched"] if row["change_kind"] == "changed"]
    assert [row["identity"]["visit_id"] for row in changed] == [expected["changed_visit"]]
    assert len(comparison["ambiguous_groups"]) == 1
    (out / "comparison.json").write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n")
    result = {"status": "PASS", "scope": "Actual installed CLI and helper functions on six new synthetic CSV files; not browser or human source review.",
              "code_sha256": code_digest(), "app_sha256": sha((ROOT / "app.py").read_bytes()), "rule_sha256": rule_hash,
              "expected_sha256": sha(expected_path.read_bytes()), "source_metadata": source, "runs": results,
              "comparison": comparison["summary"], "formula_escape": "CSV escaped; original JSON value preserved"}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
