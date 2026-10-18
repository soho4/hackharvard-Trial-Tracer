# TrialTrace — explainable draft timing checks

TrialTrace maps one spreadsheet—or accepts three prepared CSV tables—then applies
one deterministic draft timing rule and exposes unresolved evidence. The mapped
route preserves the original spreadsheet, explicit column choices and generated
tables in a complete evidence package. Review lists and saved-report comparison
remain available. The browser demonstration and the local application are working prototypes before independent pilot validation.

**Source interpretation is pending independent human review. Clinical validation is
false. Only explicit `DRAFT_ENGINEERING` execution is enabled.** A potential deviation
is a flag for human review; PASS covers only this timing check. Only synthetic inputs
are in scope; the app cannot detect or de-identify real participant data.

The public example protocol is Moderna's NCT04470427 / mRNA-1273-P301 amendment 10,
[Table 21](https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf).
It is not Regeneron data. All operational CSV examples here are newly authored synthetic records.

## Hackathon browser demonstration

The redesigned browser interface supports the one-spreadsheet workflow, clear reasons and next checks, source details, and downloadable evidence. It runs the unchanged Python engine through Pyodide, with no participant database or runtime language model. See [browser setup](web/README.md), [presenter briefing](docs/trialtrace/HACKATHON_PRESENTER.md), [research claims](docs/trialtrace/HACKATHON_CLAIMS.md), and [actual browser checks](docs/trialtrace/review/web/BROWSER_REVIEW.md).

The hosted demo is private to its owner by explicit request. Deployment, owner sign-in and a hosted demo calculation were verified; the initial sign-in failure and recovery are recorded in the browser review. The older Streamlit interface below retains three-table intake, saved-viewer and comparison features that are not in the narrow browser presentation interface.

## Launch the local upload app

The app processes uploaded bytes through the same importer, timing engine and exporter
as the CLI. It contains no canned-result or fixture fallback. Use Python 3.13 for the
fully pinned environment verified on macOS; other machines remain unverified.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-ui.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m streamlit run app.py
```

Open the printed local URL. Start with **Map one spreadsheet** and follow the
[seven-row mapping walkthrough](examples/preparation/README.md). The app generates
its internal anchors/visits/assignments files. This is a limited flat CSV path, not
a certified vendor connector; both actual dates and necessary identities must
already be present. See [research](docs/trialtrace/review/preparation/RESEARCH.md),
[validation plan](docs/trialtrace/PILOT_VALIDATION_PLAN.md) and
[demo script](docs/trialtrace/HACKATHON_DEMO.md).

For the original **Check uploaded data** tab, select the three files in `examples/browser/boundary/`,
confirm synthetic draft mode, then run the check. Use **Clear visits.csv** before
selecting `examples/browser/outside/visits.csv`: PASS becomes a potential deviation,
one day outside. Clearing removes the current result before a replacement chooser
can reject a file. No old report or download remains under new inputs.

Use the saved-report tab to inspect exported evidence in the teammate viewer.
The **Compare saved reports** tab compares two exported JSON files without changing
either report or rerunning the timing rule.
The local server binds to `127.0.0.1`; this does not deploy publicly. Stop it with Ctrl-C.
For optional local PDF provenance, append `-- --source-pdf /path/to/Prot_000.pdf` to
the Streamlit command. The app can also run without those bytes and labels that absence.

The source sidebar displays a dated snapshot fetched from the actual public
ClinicalTrials.gov API. It is study metadata and aggregate results, not participant
visit data. Every operational example is synthetic. The runtime does not fetch
registry data or send uploaded CSV records to external services.
If this optional metadata snapshot is unavailable or malformed, the sidebar says
so; a valid configured rule and the upload workflow remain usable.

## Prepare, review and compare

Follow the [synthetic workflow exercise](examples/workflows/README.md) for a fuller
example with six visits, unused invalid rows and duplicate identities.

1. Upload the three files in `examples/workflows/before/`. **File checks**
   shows missing, parsed or rejected files, record counts and diagnostics before
   calculation. Download header templates or the intake JSON when useful.
   Readable CSVs do not establish valid relationships or timing compliance.
2. Confirm synthetic draft mode and run. **Findings to review** lists non-PASS
   findings with reasons and suggested next checks. **Input rows to review** is
   separate and includes issues on unused anchors and assignments. Its count is
   issues, not visits or participants. Download either CSV list; display filters
   do not change those exports or the full evidence JSON.
3. Clear visits.csv, choose `examples/workflows/after/visits.csv`, and rerun. Save
   both evidence reports. **Compare saved reports** shows changed values and
   evidence fingerprints separately. Only complete, unambiguous identities pair;
   duplicate or incomplete identities remain unpaired. Changes in rule, source or
   producer context are visible. No missing activity or clinical resolution is inferred.
4. **Start a new check** clears the current CSVs, findings, filters and draft opt-in.
   Saved-report comparison has its own Clear controls and remains independent.

Derived CSV exports escape formula-like cells for spreadsheet use; the evidence
JSON retains exact original values. Suggested next checks are requests to inspect
evidence, not clinical decisions or completed reviews. Each saved report is limited
to 2,000,000 bytes and must pass strict validation before comparison.

## CLI install and run

Python 3.11 or later is required. Python 3.13.4 was tested. Use a regular package
installation; the tested dependency versions, including the build backend, are pinned.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m trialtrace.cli \
  --anchors examples/novel/anchors.csv \
  --visits examples/novel/visits.csv \
  --assignments examples/novel/assignments.csv \
  --rule rules/candidate_rule.json \
  --draft-synthetic \
  --output run.json
```

The example calculates target 2032-01-03, inclusive window January 3–6, and PASS
for a January 6 call. Substitute `examples/novel/visits_changed.csv`: the January 7
call produces POTENTIAL_DEVIATION, one day outside. The runtime never reads an answer key.

An optional `--source-pdf /path/to/Prot_000.pdf` records that file's exact hash.
The runtime labels this as local bytes hashed, without claiming identity validation
or human review. Without the option, the source hash is null. Technical acquisition
and identity evidence for this session is recorded separately in `docs/trialtrace/source_check/`.

Omitting `--draft-synthetic` fails closed. `DEMO_REVIEWED` in an assignment CSV cannot
authorize a reviewed run. No human approval record was created.

## Input and failure behavior

The CLI assigns the three logical roles; external filenames may vary. Headers are
exact but may be reordered. UTF-8 with optional recorded BOM, commas, standard CSV
quoting, and LF/CRLF are supported. No IDs or dates are silently repaired.

- `anchors.csv`: `study_id,participant_id,site_id,anchor_id,anchor_code,anchor_kind,anchor_date`
- `visits.csv`: `study_id,participant_id,site_id,visit_id,visit_code,event_kind,actual_date,visit_status,anchor_id,assignment_id`
- `assignments.csv`: `assignment_id,study_id,participant_id,site_id,rule_version,schedule_code,mapping_status,mapping_note`

Each table is limited to 1,000,000 bytes, 500 records and 10,000 characters per cell.
Rule JSON is limited to 65,536 bytes. Export is limited to 2,000,000 bytes; excessive
evidence causes an explicit failure, never truncation.

Every structurally valid visit produces one outcome. Broken identity/date/relationship
evidence becomes DATA_QUERY; unsupported kinds or unresolved scope become NOT_EVALUABLE.
Both have null calculations. Duplicates remain ambiguous even when identical. Invalid
unused anchors and assignments appear in `input_accounting`. No missing-event inference
or count of “clean patients” is made.

Structural/configuration errors exit 2 and write `<output>.diagnostics.json` when that
path is usable, plus structured stderr. Previous reports move to a uniquely named
`.previous/` file before a new run. Output/input collisions are refused without altering
inputs, including case aliases and hard links. A filesystem that denies writes can
prevent cleanup; such errors are reported rather than labeled successful.

## Verification and boundaries

```sh
.venv/bin/python -m pytest tests -q
.venv/bin/python tools/check_mutation.py
.venv/bin/python tools/run_acceptance.py
node tools/check_viewers.cjs
.venv/bin/python tools/run_workflow_acceptance.py --out .local-evidence/workflow-run
```

Use a new output directory for each workflow acceptance run. Reinstall the local
package after source changes before using the installed CLI or acceptance runner.
The workflow runner checks the literal expectations in the synthetic exercise;
the application never reads those expectations.

The latest application suite passed **457 tests**; the web boundary and actual browser results are recorded in `docs/trialtrace/review/web/`. The earlier workflow checkpoint passed 424 tests and its focused app regression run passed 19. Recorded commands, the actual installed-CLI workflow and fresh-wheel
reproduction are linked from [HAND_BACK](docs/trialtrace/HAND_BACK.md).
The served browser produced before/after evidence JSON and review/input-issue CSVs
byte-identical to the installed-CLI exercise. Its comparison download has equal
JSON content, with different whitespace. Malformed and oversized replacements,
recovery, independent reset and multiple rejected input roles were exercised; see
[the browser review](docs/trialtrace/review/workflows/BROWSER_REVIEW.md).
The browser also calculated and downloaded a report while optional registry metadata
was deliberately malformed, then confirmed the exact snapshot's restoration.
The embedded saved-viewer chooser timed out in this continuation, so no new viewer
browser pass is claimed; its earlier G3 Chrome evidence remains historical.
The deliberate upper-bound
mutation causes five mathematical assertion failures. Saved real input/output evidence
is in `examples/execution/`; command logs, failures and exit codes are in
`docs/trialtrace/commands/`. Node is used only for optional viewer compatibility checks.

Outputs contain exact raw-file hashes, source rows and logical ordinals, rule-byte
hashes, unique source-derived finding IDs, and a digest of the actual package source
and schema. Canonical JSON is UTF-8 with sorted keys, compact separators and one final
newline. There are no volatile timestamps in bundle content, so identical inputs,
configuration and code produce identical output bytes.

The integrated viewer preserves its upstream schema, fixtures and layout. Focused
fixes correct early-year calendar parsing and wrapping of actual engine IDs. Native
contract tests and actual served browser checks cover these repairs. The original
branch snapshot is retained under `tools/g3_viewer/native_snapshot/`; provenance and
patches are recorded beside it.

At the earlier G3 checkpoint, the main upload app was launched locally and exercised with newly authored files,
changed dates, missing evidence, malformed and oversized replacements, filters,
and actual downloads compared byte-for-byte with the CLI. Component tests are
recorded separately from browser evidence. A fresh local venv/wheel reproduction
was tested; another machine was not. See [HAND_BACK](docs/trialtrace/HAND_BACK.md) for
current gates, exact commits, review evidence, limitations, and the next action.

Current bounded workflow progress: [100/100 local checklist](docs/trialtrace/BUILD_PROGRESS.md). This is not overall clinical or production readiness.
