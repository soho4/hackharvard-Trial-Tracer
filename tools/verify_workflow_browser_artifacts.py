#!/usr/bin/env python3
"""Check preserved browser downloads; does not itself drive or certify a browser."""
import hashlib
import json
from pathlib import Path

from trialtrace.exporter import code_digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/trialtrace/review/workflows"
ACTUAL = BASE / "actual_run_final"
BROWSER = BASE / "browser_final"


def main():
    byte_pairs = [(f"{v}-browser.json", f"{v}.json") for v in ("before", "after")]
    byte_pairs += [(n, n) for n in ("before-review.csv", "after-review.csv", "before-input-issues.csv")]
    byte_pairs += [("final-app-after.json", "after.json"), ("registry-unavailable-report.json", "after.json")]
    checked = []
    for browser_name, reference in byte_pairs:
        raw = (BROWSER / browser_name).read_bytes()
        assert raw == (ACTUAL / reference).read_bytes(), browser_name
        checked.append({"file": browser_name, "reference": reference, "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(), "equality": "EXACT_BYTES"})
    for name, reference in (("before-intake.json", "before-intake.json"),
                            ("after-intake.json", "after-intake.json"),
                            ("comparison-browser.json", "comparison.json"),
                            ("final-app-comparison.json", "comparison.json")):
        raw = (BROWSER / name).read_bytes()
        assert json.loads(raw) == json.loads((ACTUAL / reference).read_bytes()), name
        checked.append({"file": name, "reference": reference, "sha256": hashlib.sha256(raw).hexdigest(),
                        "equality": "EXACT_JSON_OBJECT; whitespace is not asserted"})
    rejected = json.loads((BROWSER / "invalid-intake.json").read_bytes())
    assert not rejected["ready_for_draft_check"] and not rejected["timing_evaluated"]
    assert [item["problems"][0]["code"] for item in rejected["files"] if item["problems"]] == ["INVALID_HEADER", "INVALID_UTF8"]
    events = json.loads((BROWSER / "session-events.json").read_bytes())
    by_name = {item["event"]: item for item in events}
    assert not by_name["clear_visits_settled"]["reportDownloadVisible"]
    assert not by_name["clear_visits_settled"]["runEnabled"]
    assert not by_name["comparison_clear"]["downloadVisible"]
    assert not by_name["invalid_json_rejected"]["downloadVisible"]
    assert not by_name["oversized_json_rejected"]["downloadVisible"]
    assert not by_name["oversized_json_rejected"]["compareEnabled"]
    assert by_name["comparison_recovery"]["downloadVisible"]
    assert by_name["new_check_does_not_clear_saved_comparison"]["comparisonVisible"]
    assert by_name["null_diagnostics_repair"]["explanationVisible"]
    assert not by_name["optional_registry_restored"]["errorsSinceRepair"]
    fault = json.loads((BROWSER / "registry-fault-injection.json").read_bytes())
    assert fault["original_sha256"] == fault["restored_sha256"]
    assert fault["restored_sha256"] == hashlib.sha256((ROOT / "docs/trialtrace/review/g3_source/registry_snapshot.json").read_bytes()).hexdigest()
    result = {"status": "PASS", "scope": "Verification of actual retained browser downloads and recorded observations; not an automated browser replay.",
              "app_sha256": hashlib.sha256((ROOT / "app.py").read_bytes()).hexdigest(), "code_sha256": code_digest(),
              "checks": checked, "rejected_input_codes": ["INVALID_HEADER", "INVALID_UTF8"],
              "comparison": json.loads((BROWSER / "final-app-comparison.json").read_bytes())["summary"],
              "limitations": ["IAB embedded viewer file chooser timed out; no new embedded-viewer pass claimed.",
                              "Earlier upload interruption and null diagnostics browser errors are preserved in the review; repaired path has no later console errors.",
                              "All participant records are synthetic; no source approval or clinical validation."]}
    (BROWSER / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
