# Actual local browser workflow review

Observed on 2026-10-18 in the Codex in-app browser against the actual localhost Streamlit server. These were file chooser uploads and real downloaded files, not injected report state. All operational records are newly authored synthetic examples under `examples/workflows/`; the original public protocol was supplied to the server and hashed. This is AI engineering review, not independent human source approval.

## Evidence and versions

The browser used installed core/schema SHA-256 `5c3a04fc876cd946228433b156bfc78912b8c342011154288fda619fa08451d9`. Initial final-pass app hash was `a90a5695a105d5e89a45da41514f049726edaa3db7c1ab21c6e6f2c15c279f23`. A real console defect then required one app-only repair. Final app SHA-256 is `1068c0d08a744acbeef751873641003e495540a33e0addde0ec3feeed1b4a9d6`.

On the final app, malformed-file diagnostics, valid three-file calculation/download, saved comparison/download, optional registry corruption/recovery and console state were rechecked. The earlier byte-identical valid reports still apply to the unchanged core. `browser/` and `actual_run/` are earlier-build evidence; `browser_final/`, `actual_run_final/` and `clean_install_final/` distinguish current core results. App hashes are recorded independently from the calculation package hash.

## Observed behavior

- Before calculation, file checks show five anchor records, six visit records and six assignments. The downloadable inspection says timing was not evaluated.
- Actual before/after visit files produce 2/0/3/1 and 1/1/3/1 PASS/POTENTIAL_DEVIATION/DATA_QUERY/NOT_EVALUABLE counts. The changed date crosses the explicitly expected leap-year window by one day.
- Findings-to-review exports contain four then five findings. A separate seven-issue export retains three unused-row issues, including two reasons for one unused assignment. CSV formula-like identifiers are escaped; canonical JSON retains the exact original identifier.
- Clearing the visit file removes the old report/download and disables calculation. Replacing it with the changed file recomputes the actual results.
- Saved reports yield four unique matches, one changed record and three changes only to evidence provenance. Two duplicate visit records on each side stay unpaired. The visible table shows PASS → POTENTIAL_DEVIATION, actual 2028-03-03 → 2028-03-04 and days outside 0 → 1. This is a status transition, not clinical resolution.
- Clearing a comparison slot removes its old download. Malformed JSON produces `REPORT_JSON`; a 2,100,000-byte replacement is rejected by the upload control with comparison disabled and no old download. A subsequent valid report restores comparison.
- Starting a new CSV check resets its three slots and draft confirmation while retaining the separately uploaded saved comparison.
- Two malformed CSVs show both INVALID_HEADER and INVALID_UTF8 diagnostics. Draft confirmation does not enable calculation; no evidence report is present. The actual downloaded `invalid-intake.json` confirms both errors.
- A deliberately corrupted optional registry snapshot shows the unavailable-metadata notice. A new three-file check still runs and downloads byte-identical evidence. The original snapshot was restored and its exact hash verified; the browser again shows its actual registry label.

`browser_final/result.json` records verification of retained downloads. Before/after evidence JSON, review CSVs, input-issue CSV, final-app report and the report generated while registry metadata was unavailable match installed CLI/helper output **byte for byte**. Intake and comparison JSON match as parsed objects; the UI and runner differ in final newline formatting. `tools/verify_workflow_browser_artifacts.py` verifies these artifacts and recorded observations; it is not a browser replay script.

## Problems preserved and repaired

The malformed CSV flow called `st.json(None)` for unavailable record-link and accounting summaries. It correctly blocked calculation but produced four `react-json-view` console errors. The app now displays an explicit unavailable explanation and only sends actual objects to the JSON component. A focused AppTest regression checks the explanation, both diagnostics, absent JSON nulls, blocked calculation and absent report. The actual browser repair check at 09:20:22 UTC showed the explanation; no later warning/error logs were recorded through the restored-source check at 09:22:11 UTC. Earlier console errors remain in `session-events.json`.

Some automation interactions also failed: a stale helper did not retain initial downloads, two selectors used incorrect case/labels, one export event timed out, and local file selection twice reported an upload network error (one selected path did not yet exist; another retry used a normalized absolute path). Those attempts were not counted as successful checks. Files were re-downloaded inline, their existence/bytes verified, controls inspected and uploads retried successfully. The earlier exact-text probes of JSON error-code fragments returned false because the rendered JSON splits its strings; the accessible snapshot and downloaded inspection contain both codes. These false observations are retained rather than rewritten.

An embedded-viewer file chooser timed out in this in-app browser. No new saved-viewer browser pass is claimed here. The separately recorded historical G3 Chrome viewer checks remain the available browser evidence for that unchanged feature. Print and complete embedded PDF pagination remain unverified.

The first 424-test full-suite run overlapped the deliberate metadata corruption near its end and still passed. It is preserved, but the accepted final full-suite record is `commands/20261018T092201.707696Z-workflow-restored-snapshot-full-suite-7611b4f8/record.json`, executed after byte-exact restoration: **424 passed in 11.26 seconds**. The final fresh-environment probe is `clean_install_final/result.json`; it is same-machine AppTest/CLI evidence, not browser or second-machine evidence.

Screenshots and actual files are retained in `browser_final/`. Source review remains pending and clinical validation remains false.
