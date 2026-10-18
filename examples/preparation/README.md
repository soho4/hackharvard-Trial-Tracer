# One spreadsheet, explicit mappings

`synthetic-wide.csv` is a newly authored seven-row synthetic example. It is not a real vendor export, patient dataset or independently reviewed operational mapping. Literal expected outcomes were written before executing the mapper; they are not loaded by the application.

In **Map one spreadsheet**, upload `synthetic-wide.csv` and select:

| App field | Source column |
|---|---|
| Study identifier | trial_ref |
| Participant identifier | subject_ref |
| Site identifier | clinic |
| Safety-call record identifier | contact_ref |
| Vaccination record identifier | dose_ref |
| Actual vaccination date | dose_actual |
| Actual safety-call date | phone_actual |
| Safety-call completion status | contact_state |

Choose `done` as the exact value meaning the call actually completed. Confirm synthetic data, field meanings and draft Table 21 scope. **Prepare mapped records**, inspect the preview and declared constants, then **Run mapped draft check**.

Expected: **1 PASS, 1 POTENTIAL_DEVIATION, 4 DATA_QUERY, 1 NOT_EVALUABLE**. Record 2 is one day outside the February 29–March 3, 2028 inclusive window. Record 3 lacks an actual vaccination date. Record 4 says `entered`, which does not establish a completed call. Record 5 has an unsupported study. Records 6–7 share a call identifier and remain ambiguous.

The otherwise unused `operator_note` column and formula-like participant ID remain exact in the source file. Download the complete evidence package for original CSV, mapping manifest, generated tables and evidence JSON. Only the derived review-list CSV escapes formula-like values; the machine-input CSVs retain exact values.

The app generates the internal anchors/visits/assignments tables; you do not upload three separate files in this path. That does not prove the declaration that a participant belongs to Table 21. Both actual dates and identities must already be present on each row. Repeated vaccination IDs become duplicate-key queries, not deduplicated anchors. No missing activity, eligibility, clinical safety or amendment applicability is inferred.

To demonstrate real recalculation, edit the second record's phone_actual from 2028-03-04 to 2028-03-05 in a copy, clear the source, upload and remap: expected days outside becomes 2. Changing a mapping retires the old report and requires confirmation again. Swapping the two date columns is a plausible semantic mistake: the app cannot know the intended meaning; the independent expected-answer challenge detects it.

After installing the package, reproduce the real-file/installed-CLI exercise from the repository root (use a new output folder):

```sh
.venv/bin/python tools/run_preparation_acceptance.py --out .local-evidence/preparation-run
```

CSV contract: UTF-8, optional BOM, comma-delimited, unique nonblank headers, no surrounding header whitespace, up to 64 columns / 500 data rows / 1,000,000 bytes / 10,000 characters per cell. Dates must be exact YYYY-MM-DD. Original bytes are retained; no row filtering, date coercion or identifier trimming occurs. Export size limits can reject a complete result instead of truncating evidence.
