# What actually works, and what it proves

| Capability | Current behavior and evidence |
|---|---|
| Public study source | Real ClinicalTrials.gov API snapshot and original public protocol identity evidence; dated snapshot, not a live feed |
| CSV input | User-supplied bytes, strict parsing, exact hashes, preserved rows; no fixture fallback |
| Intake checks | Per-file missing/parsed/rejected state, byte/record counts and actionable diagnostics before calculation; header templates and intake JSON export; does not evaluate timing |
| Identity joins | Study/participant/site validation, duplicates and unresolved references exposed |
| Timing calculation | One supported Table 21 OL-D8 candidate rule; inclusive calendar-day math, tested on varied dates and new identifiers |
| Uncertainty | DATA_QUERY and NOT_EVALUABLE retain evidence and omit confident timing calculations |
| Upload app | Actual local Streamlit server, three uploads, explicit draft mode, clear-before-replacement, recalculation |
| Evidence inspection | Original rows, ordinals, hashes, selected finding, filters/search; all input accounting remains visible |
| Findings to review | All non-PASS findings with reason, source ordinal and suggested next check; full CSV export remains independent of display filters |
| Input rows to review | Separate issue list and CSV for invalid/conflicting input records, including unused anchors and assignments; counts issues rather than participants |
| JSON export | Current browser before/after downloads byte-identical to installed-CLI output; adapter uses the same functions |
| Saved-report viewer | Upstream reader integrated against unchanged contract; focused date/wrapping fixes; earlier G3 Chrome checks passed, but this continuation's in-app-browser chooser timed out and adds no new viewer pass |
| Saved-report comparison | Strict, bounded loading; uniquely identified records only; duplicate/incomplete identities remain unpaired; values, evidence fingerprints and rule/source/producer context are distinguished; originals unchanged |
| Reset/replacement | Clear selected bytes before choosing replacements; current-check reset clears files/results/filters/opt-in while saved comparison remains independent |
| Spreadsheet exports | Formula-like cells escaped in derived CSVs; canonical JSON preserves original values |
| Optional registry metadata failure | Browser fault injection showed unavailable metadata while valid draft calculation/download continued; exact original metadata restored |
| Installation | Fresh pinned Python 3.13 environment and regular wheel verified on this Mac |
| Human-reviewed rule | **Pending.** No human approval or clinical validation record exists |
| Real participant evaluation | **Unsupported.** The public registry provides no matching participant visit records; all operational inputs used here are synthetic |
| Other trials/rules, arbitrary PDFs | **Not implemented.** Unsupported event/anchor/scope records do not become confident findings |
| Missed-activity/eligibility inference | **Not implemented.** Missing records do not prove that an activity was missed |
| Clinical/regulatory decisions | **Not provided.** Potential deviations require review; PASS covers only the stated draft timing check |
| Public deployment, production auth/database | **Not performed/implemented.** Local engineering app only |

The added workflows passed the current **424-test** Python suite and an actual
installed-CLI exercise using [new synthetic files](../../examples/workflows/README.md).
A fresh same-machine wheel reproduced current code and app behavior. See
[HAND_BACK.md](HAND_BACK.md) for exact records and hashes. The current served-browser
exercise verified report and CSV byte equality, comparison JSON object equality,
malformed/oversized replacement rejection without stale downloads, recovery,
independent reset and simultaneous file diagnostics with calculation blocked.
Recovered locator/timeouts and recovered upload errors remain recorded in the
[browser review](review/workflows/BROWSER_REVIEW.md). The earlier G3 viewer-browser
results remain historical evidence for that version.

The next meaningful validation step is independent human review of the exact
protocol interpretation and independently worked examples. A future real-data
pilot also needs an explicitly authorized dataset, real mapping review, and a
separately agreed data-handling scope. More synthetic tests cannot substitute for that.
