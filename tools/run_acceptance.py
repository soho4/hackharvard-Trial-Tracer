"""Persist fresh CLI computations and independently assert their expected behavior."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

from record_command import run_record
from trialtrace.exporter import validate_bundle


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-pdf", type=Path)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[1]
    out = repo / "examples/execution"
    out.mkdir(parents=True, exist_ok=True)
    records, results = [], {}

    def run(label, folder, output, expected_exit=0, draft=True):
        command = [sys.executable, "-m", "trialtrace.cli"]
        for name in ("anchors", "visits", "assignments"):
            command += ["--" + name, str(folder / (name + ".csv"))]
        command += ["--rule", str(repo / "rules/candidate_rule.json"), "--output", str(output)]
        if draft:
            command += ["--draft-synthetic"]
        if args.source_pdf:
            command += ["--source-pdf", str(args.source_pdf.resolve())]
        record, evidence = run_record(command, repo, repo / "docs/trialtrace/commands", "core-" + label)
        records.append({"label": label, "record": str(evidence / "record.json"), "exit_code": record["exit_code"]})
        assert record["exit_code"] == expected_exit, (label, record, (evidence / "stderr.log").read_text())
        if expected_exit:
            assert not output.exists(), "Failure left a stale success report"
            return json.loads(output.with_suffix(output.suffix + ".diagnostics.json").read_text())
        bundle = json.loads(output.read_bytes())
        validate_bundle(bundle)
        assert bundle["run_mode"] == "DRAFT_ENGINEERING"
        assert bundle["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"
        for declared in bundle["input_files"]:
            assert declared["sha256"] == hashlib.sha256((folder / declared["name"]).read_bytes()).hexdigest()
        return bundle

    def inputs(name):
        folder = out / name
        folder.mkdir(exist_ok=True)
        for role in ("anchors.csv", "visits.csv", "assignments.csv"):
            shutil.copyfile(repo / "examples/novel" / role, folder / role)
        return folder

    before = inputs("before")
    first = run("novel-before", before, before / "bundle.json")
    expected = {"target": "2032-01-03", "earliest": "2032-01-03", "latest": "2032-01-06", "actual": "2032-01-06", "days_outside": 0}
    assert first["findings"][0]["calculation"] == expected
    assert first["findings"][0]["status"] == "PASS"
    repeated = run("novel-repeat", before, before / "repeat.json")
    assert first == repeated
    assert (before / "bundle.json").read_bytes() == (before / "repeat.json").read_bytes()
    after = inputs("after")
    (after / "visits.csv").write_bytes((after / "visits.csv").read_bytes().replace(b"2032-01-06", b"2032-01-07"))
    second = run("novel-changed-date", after, after / "bundle.json")
    assert second["findings"][0]["status"] == "POTENTIAL_DEVIATION"
    assert second["findings"][0]["calculation"] == {**expected, "actual": "2032-01-07", "days_outside": 1}
    assert first["run_id"] != second["run_id"]
    assert first["findings"][0]["finding_id"] != second["findings"][0]["finding_id"]
    results["date_change"] = {"before": first["findings"][0]["status"], "after": second["findings"][0]["status"], "days_outside_after": 1, "byte_identical_repeat": True}

    for label, status in (("missing_anchor", "DATA_QUERY"), ("wrong_person", "DATA_QUERY"), ("unresolved", "NOT_EVALUABLE"), ("unknown_event", "NOT_EVALUABLE")):
        folder = inputs(label)
        path = folder / ("assignments.csv" if label == "unresolved" else "visits.csv" if label == "unknown_event" else "anchors.csv")
        raw = path.read_bytes()
        if label == "missing_anchor":
            raw = raw.splitlines(keepends=True)[0]
        elif label == "wrong_person":
            raw = raw.replace(b"SYNTH-RIVER-41", b"SYNTH-OTHER-PERSON")
        elif label == "unresolved":
            raw = raw.replace(b"DRAFT_SYNTHETIC", b"UNRESOLVED")
        else:
            raw = raw.replace(b"SAFETY_PHONE_CALL", b"CLINIC_VISIT")
        path.write_bytes(raw)
        bundle = run(label, folder, folder / "bundle.json")
        assert bundle["findings"][0]["status"] == status
        assert bundle["findings"][0]["calculation"] is None
        results[label] = status

    empty = inputs("empty_visits")
    (empty / "visits.csv").write_bytes((empty / "visits.csv").read_bytes().splitlines(keepends=True)[0])
    bundle = run("empty-visits", empty, empty / "bundle.json")
    assert bundle["findings"] == [] and bundle["summary"]["visit_evaluations"] == 0
    results["empty_visits"] = 0

    stale = inputs("corrupt_replacement")
    run("stale-before", stale, stale / "bundle.json")
    prior = (stale / "bundle.json").read_bytes()
    shutil.copyfile(stale / "visits.csv", stale / "visits_before.csv")
    (stale / "visits.csv").write_bytes(b"bad,header\ninvalid,data\n")
    error = run("stale-corrupt-after", stale, stale / "bundle.json", expected_exit=2)
    assert Path(error["previous_output"]).read_bytes() == prior
    shutil.copyfile(error["previous_output"], stale / "previous_accepted.json")
    assert error["diagnostic"]["code"] == "INVALID_HEADER"
    results["corrupt_replacement"] = "EXIT_2_NO_SUCCESS_TARGET_PREVIOUS_BYTES_PRESERVED"

    error = run("reviewed-default-blocked", before, out / "reviewed_blocked.json", expected_exit=2, draft=False)
    assert error["diagnostic"]["code"] == "SOURCE_REVIEW_REQUIRED"
    frozen = run("frozen-real-files", repo / "fixtures/core_draft", out / "frozen_bundle.json")
    assert frozen["summary"]["statuses"] == {"PASS": 4, "POTENTIAL_DEVIATION": 2, "DATA_QUERY": 2, "NOT_EVALUABLE": 2}
    result = {"state": "PASS", "run_mode": "DRAFT_ENGINEERING", "source_review": "PENDING", "code_sha256": first["producer"]["code_sha256"], "results": results, "commands": records}
    (repo / "docs/trialtrace/acceptance_results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
