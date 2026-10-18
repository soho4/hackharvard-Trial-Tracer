# Verification notes

Date: 2026-10-17. Environment: Windows 11, Node v24.21.0, Python 3.14.4, Chrome 155.

## Supplied files are unchanged

`contracts/` and `fixtures/` are copied byte-for-byte from `TrialTrace_Viewer_Contracts_Fixtures.zip`. Their SHA-256 sums match the zip's `SHA256SUMS.txt`:

```
706c2b68086f1c9d38ac5ddbc37653e6f1da45d7d595eabff194c3e9737abee0  contracts/evidence_bundle.schema.json
6662c5de59443e32f4b910eaced0c65898ea41aae6754b898ea940d7ce628adc  fixtures/empty.json
aac8646b460bab7785748307d6c5f6ca20444f1186887a751e316a71e5bf2981  fixtures/invalid_duplicate_id.json
eb6782246cb37364a23c2d3847c40fdb37d4515ccbc2c8a30ff46af968ad104a  fixtures/invalid_evidence_hash.json
7895fd597aec9b715022f70d6bbea23c1059b5229397ffb742a4725b676a9bfc  fixtures/invalid_status.json
6e162b64d162b637469fe6d91751900bc838ee169a55c5fd71e2e8ad56d8a478  fixtures/markup.json
d180d1ba1a94de93519f5aa2d23f6b531a53a725620d31aa5f420041d7ae083c  fixtures/mixed.json
```

## Unit tests (F1)

Command, from the repository root:

```
node --test features/evidence_viewer/tests/contract.test.js
```

Result:

```
ℹ tests 27
ℹ pass 27
ℹ fail 0
```

Expected values in the tests are written by hand from the fixtures, not produced by the functions under test.

To check the tests can fail, four checks in `contract.js` were disabled one at a time (duplicate ID, evidence hash match, null calculation for unresolved outcomes, HTTPS-only links). Each change made the matching tests fail (26/27, 26/27, 26/27, 25/27), and restoring the file brought it back to 27/27.

## Browser tests (F2 to F4)

Served with `python -m http.server 8765 --bind 127.0.0.1` from this folder and opened at http://127.0.0.1:8765 in Chrome 155. Files were chosen through the page's real file input, one after another in the same page.

| Input | Observed |
|---|---|
| `mixed.json` | Loaded. Counts: 4 total, PASS 1, POTENTIAL_DEVIATION 1, DATA_QUERY 1, NOT_EVALUABLE 1. "4 shown / 4 findings in report". Download enabled. |
| Outcome filter DATA_QUERY | "1 shown / 4 findings in report", listing fixture-f-3. Summary counts unchanged. |
| Search `demo-p002` | "1 shown / 4", listing fixture-f-2. |
| Select fixture-f-2 | Target 2026-05-08, window 2026-05-08 to 2026-05-11, observed 2026-05-12, 1 day outside; raw record from synthetic_example.csv, ordinal 2. |
| Select fixture-f-3 | "No timing conclusion supplied."; raw `actual_date` shown as `null`. |
| Source panel | Source PDF SHA-256 "Not available"; ruleset hash labelled "declared, not verified". |
| `added_fifth_pass.json` (our file: new run_id `abinet-browser-test-005`, new finding `abinet-test-f-5`) | Total 5, PASS 2. |
| `invalid_status.json` after a valid report | Rejected: `findings[0].status: "CONFIRMED_SAFE" is not one of …`. Report hidden, download disabled, run ID and counts cleared. |
| `invalid_duplicate_id.json` | Rejected: `findings[1].finding_id: duplicate finding_id "fixture-f-1"`. |
| `invalid_evidence_hash.json` | Rejected: `findings[0].evidence[0].sha256: does not match the declared sha256 of input file "synthetic_example.csv"`. |
| `broken.json` (our file, truncated JSON) | Rejected: `file: not valid JSON (…)`. |
| `too_big.json` (our file, 2,000,001 bytes) | Rejected: `file: 2000001 bytes is over the 2000000-byte limit`. |
| `markup.json` | Loaded. `<script>` participant ID and `<img onerror>` reason shown as literal text; no `img` element created; `window.__unexpected_script_ran` stayed undefined. Source link shown as text with "Link disabled". |
| `empty.json` | All counts 0; "No findings supplied. This does not establish trial compliance."; no finding selected. |
| Download after loading `mixed.json`, with the PASS filter on | Downloaded file is byte-identical to the fixture (same SHA-256, `cmp` reports no difference). |
| Console | No errors or exceptions while loading markup, invalid and valid reports. |

Our own inputs `added_fifth_pass.json` and `broken.json` are in `tests/browser_inputs/`. `too_big.json` is not committed; it was 2,000,001 space characters, made with `node -e "require('fs').writeFileSync('too_big.json',' '.repeat(2000001))"`.

The file picker inputs and test files in the rows above were real uploads through the page. The two checks below were run differently, and are noted honestly:

- Narrow screen: the Chrome window could not be resized in this session, so the page was loaded in a 390-pixel-wide iframe and `mixed.json` was supplied to its file input through a script (same `change` handler and `file.text()` path). Result: one column, no horizontal overflow, no element extending past the frame edge.
- Out-of-order reads: in an iframe, a first file whose read was delayed 0.8 s was chosen, then a second file 50 ms later. The page showed the second file (`fast-empty.json`) and ignored the late first result.

## Not tested

- Print preview. The print stylesheet exists (hides controls, single column), but the browser print dialog was not opened.
- Opening `index.html` directly from disk (`file://`). Only the local-server launch above was tested.
- Other browsers than Chrome 155.
- Real detector output. Only the supplied hand-authored fixtures and our own variations were used.
