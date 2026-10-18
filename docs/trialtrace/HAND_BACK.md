# TrialTrace hand-back — working local draft application

TrialTrace now processes three uploaded CSV files, calculates the supported timing
check, exposes the original evidence and uncertainty, and downloads an actual
report that the integrated viewer can reopen. The app was launched and exercised
through real browser file inputs and downloads. **G3 technical checks passed for
the local draft app in Chrome. G0 human source acceptance remains blocked.**

## Run it

From the repository root, with Python 3.13:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-ui.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m streamlit run app.py
```

Open the printed local URL. Upload the three files in `examples/browser/boundary/`,
confirm synthetic draft mode and run. Vaccination 2040-02-22 produces target/earliest
2040-02-29 and latest 2040-03-03. The March 3 call passes. Clear visits.csv and choose
`examples/browser/outside/visits.csv`: the March 4 call becomes a potential deviation,
one day outside. Clearing immediately retires the old report and download.

For the broader challenge, upload the three files in
`review/g3_challenge/actual_run/inputs/` relative to this document's directory:
31 is anchors, 32 is visits and 33 is assignments. Expected counts are 9 PASS,
5 POTENTIAL_DEVIATION, 7 DATA_QUERY and 3 NOT_EVALUABLE. Inspect selected source rows,
filter/search, download the JSON and reopen it in the saved-report tab.

The source-PDF hash is optional: append `-- --source-pdf /path/to/Prot_000.pdf` to the
launch command. Without local bytes the app explicitly shows no PDF hash. The PDF
is not redistributed in this repository. A hash is not an approval.

## What “real data” means here

The original public protocol and the fetched ClinicalTrials.gov study metadata are
real. The API snapshot was fetched on 18 October 2026 with HTTP 200 and verified
TLS. It identifies NCT04470427 / mRNA-1273-P301, its sponsor and protocol document.
It contains aggregate results, not participant vaccination/call dates or assignments.
All operational records used in this application are explicitly synthetic.

There is no live participant feed, generalized PDF interpreter, clinical decision
system or validated real-patient workflow. The app enforces draft opt-in but cannot
detect or de-identify real patient data. Only synthetic inputs are in scope.
See [FEATURE_STATUS.md](FEATURE_STATUS.md) for the capability-by-capability account.

## Executed verification

| Check | Actual result |
|---|---|
| Final Python application suite | 264 passed, no skips; importer, joins, arithmetic, provenance, CLI and UI lifecycle |
| Integrated viewer tests | 58 passed, including years 0001/0004/0099 and malformed reports |
| Independent synthetic challenge | 24 newly authored visits, 14 literal calendar cases plus 10 identity/scope uncertainties; all expected results matched |
| Actual main browser | Raw uploads, changed date, missing anchor, malformed/oversized replacement, selected evidence, filters, full downloads, narrow layout |
| Standalone served viewer browser | 21 checks passed |
| Embedded Chrome workflow | 8 checks passed; main upload → compute → download → viewer upload → original download; no page/console errors |
| Download versus installed CLI | Both browser paths preserved exactly 77,329 bytes, including when the main screen showed only one filtered finding |
| Clean installation | Fresh pinned venv and regular wheel, Python -I outside checkout, exact installed core/schema, CLI/adapter/UI lifecycle pass on this Mac |
| Current core acceptance | Re-executed successfully, including changed dates, uncertain joins, empty input, stale output and reviewed-mode refusal |

The exact download SHA-256 is
`133c65689a864a9c7f9971cee38f096ac4e7117075aba2de1a19bdaafc002acd`.
Literal expected answers were authored independently of the engine. Runtime code
does not read answer keys or substitute canned results. The earlier isolated
upper-bound mutation produced five mathematical assertion failures; its evidence
is retained under `mutation/` and the timing implementation is unchanged.

Key evidence:

- `gates/G3_TECHNICAL.json` and `STATE.json`: current technical and source states.
- `commands/20261018T084350.963706Z-g3-final-application-tests-repaired-5b811e23/`:
  final 264-test command, stdout/stderr and exit code.
- `review/g3_browser/REVIEW.md`: actual in-app browser observations and failure/fix evidence.
- `review/g3_viewer/REVIEW.md` and `embedded_REVIEW.md`: native and integrated browser checks.
- `review/g3_challenge/REPORT.md`: new files, literal expectations, provenance and corrupt replacements.
- `review/g3_clean_install/REPRODUCTION.md` and `result.json`: final clean environment.
- `review/g3_source/`: actual public metadata fetch and technical review.

AppTest component checks are labeled separately from browser tests. Historical
failures and earlier-code green results remain dated evidence, not current claims.

## Defects found and fixed

Browser testing found that a client-rejected oversized replacement could leave an
old success visible. Explicit selected-file slots now require Clear before replacement,
retiring both stored bytes and report. An initial disabled-widget repair discarded
uploads; independent review caught it and the final implementation passed retesting.
Filtering could also leave the selected label on a different finding than its evidence;
the widget identity now follows the available finding IDs, verified in the browser.

The teammate viewer was imported from commit
`1b216519e93866bca3fc36be174ec0f5bf05f793`. Two focused fixes correct JavaScript's
early-year remapping and narrow-screen wrapping of engine IDs. Original schema,
fixtures, layout and upstream snapshot are preserved; its branch was not changed.

## Remaining limits and the next meaningful step

This is one working draft timing rule: Table 21's documented OL-D8 safety phone call,
anchored to an explicitly mapped actual OL-D1 vaccination, using candidate +7 through
+10 calendar days inclusive. It does not establish eligibility, complete safety
assessment, missing activities, other trial rules, or accepted protocol deviations.

Human review must independently inspect the exact public protocol and candidate,
verify the cohort, event/anchor meaning, zero early allowance and inclusive endpoints,
and resolve the table/note-number discrepancy recorded in `source_check/`.
No human identity, timestamp, checkbox, signature or approval was invented.

- Source PDF SHA-256: `da946b1ae23d40c41b332f1d0cb3311f0634e57009b4a37b9c6d6c60ee8bf186`
- Unchanged candidate SHA-256: `f36336df90a1793a80b92f48ce273488a091547110856bdcc602587ddad9e7f0`
- Core/schema digest: `eb7350f8c7adef275604cfc03b2c27fe8d1c0dd0b4a794f9bf39e41bbc80ebc2`
- Final app SHA-256: `6ab33e3e3f7253b16e2226ab4037fba904e958b9f2ced15de18d34cb9f092a9e`

A real-data pilot would additionally require an explicitly authorized dataset,
reviewed mappings and an agreed data-handling scope. The AI engineering challenge
does not satisfy G4 human review. Clean reproduction was on this Mac, not a second
machine. The in-app browser did not expose an iframe download event; standard Chrome
verified that download's exact bytes. Its cause remains unverified. Print CSS passed,
but OS printing and complete embedded PDF pagination were not tested.

## Delivery and repository

Verified origin: `https://github.com/soho4/hackharvard-Trial-Tracer`.
Feature branch: `codex/trialtrace-core-v4`. The preceding core delivery was
`27f825450212d14269ee04bfdf494fe5245f481b`.

The delivery manifest outside the commit records the exact final HEAD, push result,
remote SHA and archive hashes; a commit cannot embed its own hash. Raw protocol PDF,
raw API response, personal/historical handoff, credentials and environments stay out
of commits. No default-branch merge, public deployment, spending, real-patient use,
clinical validation or ongoing background work is claimed. The local browser test
server is stopped during delivery teardown; use the command above to relaunch it.
