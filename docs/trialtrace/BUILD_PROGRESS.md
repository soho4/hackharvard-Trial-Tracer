# Build progress — 2026-10-18

The defined **local synthetic workflow milestone is complete: 100/100 weighted acceptance points**, up from the recorded 75/100 baseline. This is a checklist score for the bounded local demo, not an estimate that the overall clinical application is complete, percent of development effort, or a measure of clinical readiness.

The denominator is unchanged from [the baseline rubric](review/workflows/BASELINE_REVIEW.md). Evidence, including repaired failures and browser limitations, is in [the browser review](review/workflows/BROWSER_REVIEW.md), [artifact verification](review/workflows/browser_final/result.json), [installed-file exercise](review/workflows/actual_run_final/result.json) and [fresh-environment probe](review/workflows/clean_install_final/result.json).

| Local workflow | Weight | Before | Now | Acceptance evidence |
|---|---:|---:|---:|---|
| Trustworthy draft computation | 30 | 30 | 30 | 424 current tests; pinned rule/schema unchanged; actual browser/CLI report bytes equal |
| Understand and prepare inputs | 15 | 10 | 15 | Per-role preflight, record counts, all independent errors, actual two-invalid-file browser check |
| Inspect findings and plan corrections | 20 | 14 | 20 | Findings list plus separate unused/input-row issues; actual formula-safe full exports and evidence selectors |
| Correct and compare saved runs | 15 | 3 | 15 | Strict validation, unique identity matching, duplicate refusal, visible field changes, real export/rejection/recovery |
| Reproduce and hand off local workflow | 20 | 18 | 20 | Documented new-file scenario, fresh installed environment, actual optional-metadata failure/recovery |
| **Total** | **100** | **75** | **100** | **Bounded engineering milestone only** |

The application actually parses supplied CSV bytes, checks the one supported candidate rule and produces evidence-linked results. No canned-result fallback or model service is involved. Public protocol bytes and dated registry metadata are real; every operational participant record remains synthetic.

The overall application remains a draft. The remaining work is not honestly reducible to a percentage without agreeing a larger scope:

- Independent human review of the exact protocol interpretation, applicability and candidate rule; G0 remains blocked.
- An explicitly authorized, appropriately handled participant dataset matching the supported rule. No real participant pilot has been performed.
- Installation and challenge by another person on another machine.
- Any additional rules require their own source evidence, implementation and acceptance cases. Arbitrary protocol interpretation is not implemented.
- Deployment, authentication, shared storage and production operations are outside the current local scope. No public deployment has occurred.

The in-app embedded-viewer chooser and download limitations remain documented; historical Chrome viewer checks passed. OS print and complete embedded PDF pagination are not established. These are disclosed limits, not claims of universal browser support.
