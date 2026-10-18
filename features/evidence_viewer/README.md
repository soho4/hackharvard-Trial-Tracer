# TrialTrace Evidence Report Viewer

A read-only page that opens a saved TrialTrace evidence report (`trialtrace.evidence.v1` JSON), checks it against the contract, and shows its findings and supporting evidence. It never re-runs the detector, recalculates dates or edits the report.

Plain HTML, CSS and JavaScript. No npm install, framework, database, account or model API.

## Run it

From the repository root:

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory features/evidence_viewer
```

On Windows, `py -3` can replace `python`. Open http://127.0.0.1:8765, click "Open evidence report" and choose a JSON report, for example `features/evidence_viewer/fixtures/mixed.json`.

## Test it

Requires Node 18 or newer (tested with Node 24.21.0):

```sh
node --test features/evidence_viewer/tests/contract.test.js
```

## Files

| File | Purpose |
|---|---|
| `contract.js` | Pure functions: `validateBundle`, `parseReportText`, `summarizeFindings`, `filterFindings`, `safeSourceURL`. No page code, so Node can test them. |
| `app.js` | Page logic: file picker, rendering, filters, download, print. |
| `index.html`, `style.css` | The single page and its styles, including narrow-screen and print layouts. |
| `contracts/evidence_bundle.schema.json` | The report schema, unchanged from the project owner's contract package. |
| `fixtures/` | The six supplied contract fixtures, unchanged (SHA-256 sums listed in VERIFICATION.md). |
| `tests/contract.test.js` | 27 Node tests: supplied fixtures plus our own cases. |
| `tests/ACCEPTANCE_CASES.md` | Acceptance cases from the contract package. |

## How it works

1. Open. The file must be 2,000,000 bytes or less and valid JSON. Choosing a new file first clears everything on screen and disables download, so a rejected file never leaves the old report visible. If a slow earlier read finishes after a newer file was chosen, its result is ignored.
2. Validate (`validateBundle`). Checks every required field and allowed value from the schema, plus the cross-record rules the schema cannot express:
   - finding IDs are unique;
   - each evidence `source_file` is listed in `input_files`, with the same declared SHA-256;
   - input file names are unique;
   - each outcome agrees with its calculation: PASS has 0 days outside, POTENTIAL_DEVIATION has more than 0, DATA_QUERY and NOT_EVALUABLE have no calculation;
   - dates are real calendar dates (the schema pattern alone would accept 2026-02-30).

   An unknown `schema_version` is rejected before anything else. Any error rejects the whole file, and every error is listed.
3. Summarize (`summarizeFindings`). The five counts are computed from the findings array each time; nothing is hard-coded.
4. Filter (`filterFindings`). Outcome filter plus case-insensitive search over finding, participant, site and visit IDs, visit code and reason. The page always shows "N shown / M findings in report"; the summary counts always cover the whole report.
5. Show evidence. Identifiers (null shown as "Not supplied"), the supplied reason, the recorded calculation as supplied (or "No timing conclusion supplied"), and each supporting raw record.
6. Download and print. Download hands back the uploaded file object itself, so the bytes are identical to what was opened. Print uses a print stylesheet; the data shown does not change.

## Safety

- Report text is always inserted with `textContent`, never `innerHTML`. Nothing from a report is evaluated or rendered as HTML.
- A source link is clickable only if it is `https:` with no user name or password, and it opens with `rel="noopener noreferrer"`. Anything else is shown as text with a "Link disabled" note.
- SHA-256 values are declared metadata. The viewer checks their format and that they agree with each other; it cannot verify the original files and labels them "declared, not verified". A null source PDF hash is shown as "Not available".

## Where this connects

The only connection to the rest of TrialTrace is the saved report format. The detector, or an exporter beside it, writes a `trialtrace.evidence.v1` file; this viewer reads it. The viewer imports nothing from the detector, and the detector imports nothing from the viewer.

## Limits

- Synthetic reports only (`data_kind` must be `SYNTHETIC` and `clinical_validation` must be `false`).
- The supplied fixtures are hand-authored contract examples. The real detector's output has not yet been run through this viewer.
- See VERIFICATION.md for what was and was not tested in a browser.
