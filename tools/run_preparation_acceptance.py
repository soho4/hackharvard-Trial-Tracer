#!/usr/bin/env python3
"""Actual source file -> mapped tables -> installed CLI parity and full archive."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from record_command import run_record
from trialtrace.cli import load_rule
from trialtrace.exporter import code_digest
from trialtrace.preparation import prepare_spreadsheet, evidence_package

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, default=ROOT / "examples/preparation/mapping.json")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = (ROOT / "examples/preparation/synthetic-wide.csv").read_bytes()
    profile = json.loads(args.mapping.read_bytes())
    expected = json.loads((ROOT / "examples/preparation/expected.json").read_bytes())
    rule, rule_hash = load_rule(ROOT / "rules/candidate_rule.json")
    prepared = prepare_spreadsheet(source, "synthetic-wide.csv", profile["columns"], profile["completed_value"], rule, rule_hash, scope_confirmed=True)
    bundle, encoded, package = evidence_package(prepared, rule, rule_hash)
    (out / "evidence.json").write_bytes(encoded)
    (out / "evidence-package.zip").write_bytes(package)
    (out / "preparation.json").write_text(json.dumps(prepared["manifest"], indent=2) + "\n")
    assert [f["status"] for f in bundle["findings"]] == expected["statuses"]
    assert bundle["summary"]["statuses"] == expected["counts"]
    assert bundle["findings"][1]["calculation"] == expected["second_calculation"]
    command = [sys.executable, "-I", "-m", "trialtrace.cli", "--draft-synthetic", "--rule", str(ROOT / "rules/candidate_rule.json")]
    for name, (_, raw) in prepared["uploads"].items():
        target = out / name
        target.write_bytes(raw)
        command += ["--" + name.removesuffix(".csv"), str(target)]
    target = out / "cli-evidence.json"
    command += ["--output", str(target)]
    record, folder = run_record(command, ROOT.parent, out / "commands", "mapped-installed-cli")
    assert record["exit_code"] == 0, folder
    assert target.read_bytes() == encoded
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert archive.testzip() is None
        assert archive.read("source.csv") == source
        assert archive.read("evidence.json") == encoded
    result = {"status": "PASS", "code_sha256": code_digest(), "app_sha256": hashlib.sha256((ROOT / "app.py").read_bytes()).hexdigest(),
              "source_sha256": hashlib.sha256(source).hexdigest(), "evidence_sha256": hashlib.sha256(encoded).hexdigest(),
              "package_sha256": hashlib.sha256(package).hexdigest(), "counts": bundle["summary"]["statuses"],
              "original_bytes_preserved": True, "installed_cli_bytes_equal": True,
              "scope": "Actual newly authored synthetic wide CSV; not an actual vendor export, real-patient pilot or human source review."}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
