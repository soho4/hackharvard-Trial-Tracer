# Prepare, review, correct and compare — synthetic workflow exercise

These are six newly authored CSV files for engineering checks. They do not contain
participant records. `expected.json` contains literal expectations written before
running the implementation; the application never reads that file.

1. Upload the three files under `before/`. Inspect the file checks before running.
   There are 5 anchor records, 6 visit records and 6 assignments. Structurally valid
   records can still have missing, conflicting or unsupported evidence.
2. Confirm synthetic draft mode and run. Expected counts are 2 PASS, 0 potential
   deviations, 3 data queries and 1 not evaluable. Download the full evidence JSON.
3. Inspect the finding list and the separate input-issue list. The latter includes
   unused invalid rows and has 7 issues, not 7 participants. Download both CSV lists.
4. Clear visits.csv and select `after/visits.csv`; the other two files are identical.
   Only `SYNTH-FLOW-V1` has a changed actual date: March 3 becomes March 4, 2028.
   Rerun and save the new evidence JSON. That record changes from PASS to a potential
   deviation, one day outside February 29 through March 3 inclusive.
5. Open Compare saved reports. Choose the first and second downloaded JSONs.
   Four records have unique identities; one has changed values and three have only
   evidence-fingerprint changes. Both duplicate-key records remain unpaired on each
   side. No new/missed event or resolved clinical deviation is inferred.
6. Download the comparison. Clear one report and select malformed JSON to verify
   that the previous comparison and its download cannot survive rejection.

The first participant identifier deliberately begins with `=`. It must remain exact
in the evidence JSON and appear with a leading apostrophe in the derived review CSV
so spreadsheet applications do not interpret it as a formula.

`tools/run_workflow_acceptance.py --out <new-evidence-directory>` runs the same input
files through the installed CLI and helpers. A separate served-browser review is
required for UI claims. All source interpretation remains pending human review.
