# Current hand-back: explicit spreadsheet preparation

The new first tab, **Map one spreadsheet**, lets a user identify eight source columns, choose the exact completed-call value, review a preview and run the existing draft check. A downloadable package preserves the original source and complete transformation chain. The original three-table, review-list and saved-comparison routes remain.

**Current stage: local synthetic prototype before independent pilot validation.** No overall completion percentage or measured saving is claimed. Research found that existing EDC systems already provide rules/scheduling and exports vary by study configuration. The portable evidence-review workflow is a hypothesis to validate, not an established unmet need.

Follow [the mapping walkthrough](../../examples/preparation/README.md). Expected seven-row outcome: 1 PASS, 1 POTENTIAL_DEVIATION, 4 DATA_QUERY, 1 NOT_EVALUABLE. The dataset is authored synthetic CSV, not a vendor export. The app generates the three internal tables from explicit declarations; it does not prove amendment/cohort applicability.

**Verification:** 447 tests passed; actual browser ZIP/JSON/review CSV match installed engine artifacts; a fresh isolated regular-wheel environment reproduced the current code and app. A deliberately swapped date mapping failed the literal-answer challenge as intended. Three browser upload transport errors remain recorded, with subsequent successful upload and parser rejection; no root-cause fix is claimed.

[Current acceptance](review/preparation/ACCEPTANCE.md) · [Research](review/preparation/RESEARCH.md) · [Technical gate](gates/PREPARATION_TECHNICAL.json) · [Progress](BUILD_PROGRESS.md) · [Demo script](HACKATHON_DEMO.md) · [Pilot validation plan](PILOT_VALIDATION_PLAN.md).

G0 independent human source review remains blocked; clinical validation is false. No actual participant dataset, interviews, measured savings or public deployment. Next external evidence: a synthetic export from a real configured workflow plus its dictionary, independently checked mappings/rule and a measured review exercise. No one has been contacted on the user's behalf.

The final commit, verified remote SHA and delivery archive hashes are recorded in the external delivery manifest. Run commands below still apply. The rest of this file is the **historical preceding workflow hand-back**, with its original hashes and counts retained as history rather than current results.

---

# TrialTrace hand-back — working local draft application

TrialTrace now checks uploaded files before calculation, computes the supported
timing rule, and exposes original evidence, findings to review and separate input-row
issues. Two saved reports can be compared without changing their contents or
rerunning the rule. **G0 human source acceptance remains blocked; clinical
validation is false.**

The earlier G3 local draft app passed real Chrome upload/download checks. The added
intake, review-list and comparison workflows now have current served-browser,
component, CLI and fresh-installation evidence below. The embedded saved-viewer
chooser timed out in this continuation; no new viewer-browser pass is claimed.

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

For the new preparation/review/comparison exercise, follow
[examples/workflows/README.md](../../examples/workflows/README.md). Upload the
`before/` files and inspect **File checks** before opting into calculation. The run
has six visits: 2 PASS, 0 POTENTIAL_DEVIATION, 3 DATA_QUERY and 1 NOT_EVALUABLE.
**Findings to review** has four non-PASS rows; **Input rows to review** separately
has seven issues, including three issues on unused records. These are issue counts,
not counts of participants. Both CSV exports cover the whole report regardless of
display filters; formula-like cells are escaped while JSON values stay exact.

Save the first JSON, clear visits.csv, and use `after/visits.csv`. One actual date
changes from March 3 to March 4, 2028, becoming one day late. Save the second JSON
and open **Compare saved reports**. Four records match uniquely: one has changed
values and three have evidence-fingerprint changes only. Two duplicate-key records
on each side remain unpaired. Rule/source/producer differences are exposed; this
does not infer missed activities, clinical improvement or human resolution.
**Start a new check** resets current files, filters, findings and draft opt-in;
the saved comparison has its own independent Clear controls.

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

Current workflow continuation:

| Check | Actual result |
|---|---|
| Full Python suite | **424 passed in 11.26 s**, exit 0, after exact registry-snapshot restoration; current importer/engine, intake, worklists, comparison, metadata and app lifecycle |
| Final app components | **19 passed in 5.80 s**, including the final unavailable-intake-summary regression; component tests, not browser evidence |
| Accounting/comparison regression | **97 passed in 0.45 s**; contradictory optional accounting rejected and duplicate visit keys remain unpaired |
| Actual installed-CLI exercise | Six new synthetic CSV files, literal expectations, before/after report bytes equal to adapter output, full finding/input-issue exports and comparison all matched |
| Fresh installation | Pinned Python 3.13.4 environment and regular wheel outside the checkout; exact current source/schema and app hashes, CLI/adapter/UI lifecycle pass on this Mac |
| Added-workflow browser checks | Actual uploads/downloads; before/after evidence and review/input-issue CSVs byte-identical to installed-CLI exercise; comparison JSON object-equal with whitespace differences |
| Browser rejection/recovery | Malformed report gives REPORT_JSON without stale download; over-2-MiB report rejected without comparison/download; recovery passes; reset retains independent saved comparison; two invalid CSV roles show diagnostics and block calculation even with draft confirmed |
| Browser optional-metadata fault | Deliberately malformed registry snapshot showed unavailable metadata while valid CSV calculation/download continued; original bytes and source label restored |

The installed-CLI exercise and both fresh-install probes used core/schema
`5c3a04fc876cd946228433b156bfc78912b8c342011154288fda619fa08451d9`
and unchanged engine behavior. The final fresh-install app probe used app
`1068c0d08a744acbeef751873641003e495540a33e0addde0ec3feeed1b4a9d6`.
The preceding app/CLI record used
`a90a5695a105d5e89a45da41514f049726edaa3db7c1ab21c6e6f2c15c279f23`,
before the display-only null-summary repair; it remains preserved with that hash.
Reproduce the exercise after installing the current package:

```sh
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python tools/run_workflow_acceptance.py --out .local-evidence/workflow-run
```

Choose a new output directory for each run; optional `--source-pdf` adds the supplied
local PDF's hash. The runner uses literal expectations; the application does not.

Current evidence:

- [Final restored-snapshot full suite](review/workflows/commands/20261018T092201.707696Z-workflow-restored-snapshot-full-suite-7611b4f8/record.json) and adjacent stdout/stderr; the earlier 423-test checkpoint and the 424-test run overlapping intentional metadata fault injection remain preserved separately.
- [Final app component regression](review/workflows/commands/20261018T092020.059769Z-null-intake-json-regression-verified-fbdac420/record.json); the [earlier 71-test app/registry record](review/workflows/commands/20261018T091111.330862Z-workflow-current-source-app-registry-final-e561cc58/record.json) retains its original source binding.
- [Actual workflow result](review/workflows/actual_run_final/result.json), before/after reports, intake, CSV exports, comparison and nested CLI commands.
- [Final fresh-install app probe](review/workflows/clean_install_final/result.json), following the [fresh environment/wheel creation](review/workflows/clean_install/result.json), with exact dependency/source hashes and isolated CLI records.
- [Browser review](review/workflows/BROWSER_REVIEW.md) and [browser result](review/workflows/browser_final/result.json), with actual downloads and recorded interaction limitations.
- [Baseline workflow review](review/workflows/BASELINE_REVIEW.md) and [integration review](review/workflows/INTEGRATION_REVIEW.md), including historical failures and literal expected-answer checks.

Current browser evidence JSON sizes are 20,754 bytes before and 20,771 bytes after;
their hashes are respectively
`7a402a5ad58cbf3b6dcf981814e6a4f490933af8fdbd0ea029838a7ff5244a36`
and `51db5c6548cf19324cfc08b198445be0eb7c52ae6e384b1d0a4c008794bb3c54`.
Both finding-list downloads and the downloaded before-input-issue list are exactly
equal to their generated counterparts. Comparison equality is of parsed JSON
content, not bytes. Occasional automation locator/timeouts and recovered upload
errors were recovered and retained in the browser record. The embedded saved-viewer
chooser timeout remains a limitation; the earlier G3 Chrome viewer check below is
not presented as a new pass.
The final app's valid calculation/comparison was rechecked after the JSON-null
display repair. Registry fault injection at 09:21:33 UTC left the draft run usable;
the exact original snapshot was restored at 09:21:57 UTC and its browser label was
observed again at 09:22:11 UTC. That last observation recorded no browser errors
since the repair. The [fault record](review/workflows/browser_final/registry-fault-injection.json)
and session events preserve the original/restored hash and timing.

Earlier G3 checkpoint, retained as historical evidence:

| Check | Actual result |
|---|---|
| Earlier Python application suite | 264 passed, no skips; importer, joins, arithmetic, provenance, CLI and UI lifecycle |
| Integrated viewer tests | 58 passed, including years 0001/0004/0099 and malformed reports |
| Independent synthetic challenge | 24 newly authored visits, 14 literal calendar cases plus 10 identity/scope uncertainties; all expected results matched |
| Actual main browser | Raw uploads, changed date, missing anchor, malformed/oversized replacement, selected evidence, filters, full downloads, narrow layout |
| Standalone served viewer browser | 21 checks passed |
| Embedded Chrome workflow | 8 checks passed; main upload → compute → download → viewer upload → original download; no page/console errors |
| Download versus installed CLI | Both browser paths preserved exactly 77,329 bytes, including when the main screen showed only one filtered finding |
| Clean installation | Fresh pinned venv and regular wheel, Python -I outside checkout, exact installed core/schema, CLI/adapter/UI lifecycle pass on this Mac |
| Earlier core acceptance | Re-executed successfully, including changed dates, uncertain joins, empty input, stale output and reviewed-mode refusal |

That earlier G3 download's SHA-256 is
`133c65689a864a9c7f9971cee38f096ac4e7117075aba2de1a19bdaafc002acd`.
Literal expected answers were authored independently of the engine. Runtime code
does not read answer keys or substitute canned results. The earlier isolated
upper-bound mutation produced five mathematical assertion failures; its evidence
is retained under `mutation/` and the timing implementation is unchanged.

Earlier G3 evidence:

- `gates/G3_TECHNICAL.json`: historical G3 gate; `STATE.json` and `gates/WORKFLOW_TECHNICAL.json` hold the current state.
- `commands/20261018T084350.963706Z-g3-final-application-tests-repaired-5b811e23/`:
  the 264-test checkpoint command, stdout/stderr and exit code.
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

The workflow continuation found and fixed two additional robustness defects:
corrupt optional registry metadata could prevent the upload UI from rendering, and
saved-report input-accounting claims could contradict evidence actually present in
the report. The metadata loader now returns a structured failure that the sidebar
handles without fabricated fallback. Accounting validation rejects contradictions
before lists or comparisons use them. Tests preserve the failures and repairs.
Worklists now put outcome, participant, visit, reason and next check before internal
identifiers; detailed references remain in exports and evidence views.

A final browser console check found that rendering unavailable intake summaries as
JSON null emitted viewer errors. The app now explains that record-link checks are
unavailable until all three files are readable. The regression test requires the
caption, no JSON-null component, and calculation to stay blocked. This display fix
does not change core code, rule semantics or report bytes.

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
- Current core/schema digest: `5c3a04fc876cd946228433b156bfc78912b8c342011154288fda619fa08451d9`
- Current app SHA-256: `1068c0d08a744acbeef751873641003e495540a33e0addde0ec3feeed1b4a9d6`

The historical G3 checkpoint used core/schema
`eb7350f8c7adef275604cfc03b2c27fe8d1c0dd0b4a794f9bf39e41bbc80ebc2`
and app `6ab33e3e3f7253b16e2226ab4037fba904e958b9f2ced15de18d34cb9f092a9e`;
those hashes remain associated with their original browser evidence.

A real-data pilot would additionally require an explicitly authorized dataset,
reviewed mappings and an agreed data-handling scope. The AI engineering challenge
does not satisfy G4 human review. Clean reproduction was on this Mac, not a second
machine. The in-app browser did not expose an iframe download event; standard Chrome
verified that download's exact bytes. Its cause remains unverified. Print CSS passed,
but OS printing and complete embedded PDF pagination were not tested.

## Delivery and repository

Verified origin: `https://github.com/soho4/hackharvard-Trial-Tracer`.
Feature branch: `codex/trialtrace-core-v4`. The preceding G3 delivery was
`7bcf96a461815ed907902d7373f056810b0d178a`; the earlier core delivery was
`27f825450212d14269ee04bfdf494fe5245f481b`.

The delivery manifest outside the commit records the exact final HEAD, push result,
remote SHA and archive hashes; a commit cannot embed its own hash. Raw protocol PDF,
raw API response, personal/historical handoff, credentials and environments stay out
of commits. No default-branch merge, public deployment, spending, real-patient use,
clinical validation or ongoing background work is claimed. The earlier G3 test server
was stopped during its delivery teardown. The current continuation's launch and
teardown status belongs in its delivery record; use the command above to launch locally.

Current bounded workflow progress: [100/100 local checklist](BUILD_PROGRESS.md). This is not overall clinical or production readiness.
