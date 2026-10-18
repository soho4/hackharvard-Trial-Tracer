# Research log

Technical observations only; no human source approval.

- 2026-10-18 UTC: Python CSV docs https://docs.python.org/3.13/library/csv.html checked for newline handling, string-preserving records, and strict errors. Use newline="" and explicit header/width checks; add quote-state scanning because strict parser alone allows stray unquoted quotes. Tests cover both.
- Python datetime docs https://docs.python.org/3.13/library/datetime.html checked for calendar date arithmetic and representable date bounds. Exact regex precedes fromisoformat; overflow becomes row query.
- jsonschema validator docs https://python-jsonschema.readthedocs.io/en/stable/validate/ checked for Draft202012Validator usage. Schema cannot enforce cross-record provenance or real dates, so explicit semantics will supplement it.
- Exact protocol acquisition and technical visual observations are in source_check/SOURCE_CHECK.md. G0 remains blocked; preserve note-number discrepancy for human review.

- Actual origin/abinet/evidence-viewer at 1b216519e93866bca3fc36be174ec0f5bf05f793: schema and six fixtures exactly match the handoff. Both isolated validators accept eight current normal-date reports. Direct probes show Date.UTC remaps years 0-99 in the teammate validator, causing 0001/0099 rejection; unchanged reference validator and core accept those valid dates. Source and probe evidence: review/core/viewer_year_results.json. Preserve teammate source; fix in G3.
- Independent technical review found duplicate-evidence amplification, 140k-cell diagnostic ambiguity, malformed CLI/stale-output errors, unpaired-surrogate configuration, abbreviated flags and case/hardlink collisions. Each received targeted regression tests or actual filesystem probes and passed recheck; see review/core/REVIEW.md. This is AI technical review, not independent human source approval.
- Fresh venv with locked dependencies and a regular wheel: imported installed package outside checkout with Python -I, verified exact schema and source digest, and reproduced current CLI output bytes. clean_install.json records versions and paths. No another-machine claim.

## G3 continuation, 18 October 2026

- Actual official registry API https://clinicaltrials.gov/api/v2/studies/NCT04470427
  returned HTTP 200 with TLS verification. Its protocol identity/date/size agree
  with the candidate and previously acquired PDF. The fetched metadata and hash
  are in review/g3_source/registry_snapshot.json; raw response stays local. The
  registry provides aggregate results and no matching individual visit/assignment
  records. The app displays a dated source card, never a fabricated patient feed.
- Official Streamlit file-uploader documentation
  https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader and
  installed 1.66.0 signatures were checked for upload bytes, callbacks and limits.
  Actual browser testing showed that an oversized replacement is rejected before
  the Python callback. The selected-file/explicit-Clear design follows that observed
  lifecycle rather than assuming every attempted replacement reaches Python.
- Official iframe documentation https://docs.streamlit.io/develop/api-reference/layout/st.iframe
  and installed API were checked for inline trusted viewer HTML. Replacing the
  deprecated components.html call removed its warning; fresh AppTest and actual
  served Chrome checks passed for the final app fingerprint.
- JavaScript early-year validation was checked with literal years 0001, 0004 and
  0099. setUTCFullYear avoids Date.UTC's 0–99 remapping. Year 0000 remains invalid;
  schema and the candidate window are unchanged. Fifty-eight viewer tests passed.
- Actual standard Chrome captured the embedded viewer Blob download and verified
  exact original bytes. The same capture did not succeed in the in-app browser;
  the cause is unverified. Print CSS was exercised, but no OS print/PDF-pagination
  claim is made. See review/g3_viewer/embedded_REVIEW.md.
- The final app was verified against the installed CLI and a fresh Python -I wheel
  installation. New evidence lives under review/g3_clean_install; the earlier
  clean_install.json is retained as its original core-only checkpoint.

## Local workflow continuation, 18 October 2026

- Inspected the current specification, app and parser/accounting contract before
  extending the local engineering workflow. Intake uses the same strict parser as
  calculation and reports independently rejected files before draft execution.
  Record links and accounting do not establish timing outcomes. The read-only
  baseline and acceptance risks are preserved in
  [review/workflows/BASELINE_REVIEW.md](review/workflows/BASELINE_REVIEW.md).
- A findings-only list misses invalid unused anchors and assignments. The workflow
  therefore exposes a separate input-issue list, with one row per issue and explicit
  unused-row context. Full exports preserve finding/record references independently
  of UI filters. Formula-like identifiers are escaped only in derived CSVs; original
  JSON evidence is unchanged. Newly authored synthetic CSVs and independently
  worked expectations are in [examples/workflows](../../examples/workflows/README.md).
- Cross-run finding IDs include the input snapshot and cannot identify the same
  activity after an input change. Comparison instead requires unique, complete
  study/participant/site/visit identities, leaves duplicate visit keys unpaired,
  and distinguishes changed values from evidence-only changes. Missing identity
  is not recovered from registry metadata; an unpaired record does not establish
  a missed activity. Saved reports are read without recalculating timing.
- Adversarial saved-report checks found that structurally plausible accounting
  could contradict source evidence already present in findings. The shared
  validator now checks that consistency. The actual reproduction, intermediate
  failed test edit and final **97-pass** accounting/comparison run are preserved
  under `review/workflows/commands/`; these are technical tests, not source approval.
- Read-only component fault injection showed that malformed optional registry
  metadata could stop the whole upload UI. A bounded strict loader now validates
  declared NCT/API identity, types and date shapes, rejects malformed/deep/duplicate
  JSON and invalid Unicode, and returns structured errors. The app reports metadata
  unavailable while retaining a valid draft workflow. This does not authenticate
  the snapshot's declaration or replace human review of the protocol.
- The pre-null-summary-repair full Python command passed **423 tests in 11.10 s**, exit 0, at
  [the recorded full-suite run](review/workflows/commands/20261018T091034.290277Z-workflow-final-all-tests-f717f286/record.json).
  The later focused app/registry run passed **71 tests in 5.13 s** with explicit
  `PYTHONPATH=src` and stable before/after hashes. Its
  [source binding](review/workflows/commands/20261018T091111.330862Z-workflow-current-source-app-registry-final-e561cc58/source_binding.json)
  records app `a90a5695...` and code/schema `5c3a04fc...`.
- A standalone review wrapper initially imported an older installed package even
  though pytest selected repository `src` through its configuration. Those two
  intermediate bindings are retained and explicitly qualified in the baseline
  review. The final binding hashes repository files directly. The current
  [installed-CLI exercise](review/workflows/actual_run_final/result.json) and
  [fresh regular-wheel reproduction](review/workflows/clean_install/result.json)
  independently record exact current package/app hashes and expected results.
  Reinstall after source changes before using a previously installed package.
- No new public-source fetch, patient dataset or human review was added in this
  continuation. The actual public protocol and dated registry snapshot remain
  distinct from synthetic operational examples.
- The final served-browser workflow downloaded before/after evidence JSON and
  finding/input-issue CSVs that match the installed-CLI exercise byte-for-byte.
  Comparison JSON objects are equal while whitespace differs. Malformed saved
  JSON produced structured REPORT_JSON with no stale download; a report above
  2 MiB was rejected without comparison/download and valid replacement recovered.
  Resetting current CSV checking retained the independent comparison. Two invalid
  input roles displayed their own diagnostics and blocked calculation with draft
  mode confirmed. See [BROWSER_REVIEW.md](review/workflows/BROWSER_REVIEW.md) and
  [the result record](review/workflows/browser_final/result.json).
- Occasional computer-use locator/timeouts and recovered upload errors were
  recovered and remain recorded. The in-app browser's embedded saved-viewer
  chooser timed out in this continuation. That adds no new viewer-browser pass;
  earlier G3 Chrome viewer evidence remains associated with its historical version.
- Final browser console inspection found JSON-viewer errors when malformed inputs
  left relationship/accounting summaries unavailable. Rendering an explicit caption
  instead of JSON null repairs that display path. The final app fingerprint is
  `1068c0d08a744acbeef751873641003e495540a33e0addde0ec3feeed1b4a9d6`;
  core/schema remains `5c3a04fc...`. The
  [final 19-test app regression](review/workflows/commands/20261018T092020.059769Z-null-intake-json-regression-verified-fbdac420/record.json)
  passed in 5.80 seconds, and the
  [fresh-install probe rerun](review/workflows/clean_install_final/result.json)
  passed with that exact app hash. Earlier `a90a5695...` evidence retains its original
  fingerprint rather than being relabeled as the final revision.
- A deliberate served-browser registry fault replaced the optional snapshot with
  malformed JSON at 09:21:33 UTC. The sidebar reported metadata unavailable while
  valid synthetic CSV calculation and an actual report download succeeded. The
  original bytes were restored at 09:21:57 UTC with identical SHA-256
  `1406d7f7451506be41d1056b201d3baf46e1055885282ca7495ae5df3899dd4d`.
  At 09:22:11 UTC the browser showed the source label again and no errors since
  the null-summary repair. The [fault record](review/workflows/browser_final/registry-fault-injection.json)
  and adjacent downloaded report/session events preserve that observation.
- The first final 424-test run overlapped the deliberate optional-metadata fault
  and remains preserved. After exact snapshot restoration, the
  [normal-state final suite](review/workflows/commands/20261018T092201.707696Z-workflow-restored-snapshot-full-suite-7611b4f8/record.json)
  passed **424 tests in 11.26 seconds**, exit 0. This is the final full-suite claim,
  separate from the earlier 423-test and focused component checkpoints.
