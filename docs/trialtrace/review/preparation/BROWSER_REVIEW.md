# Served browser review — 18 October 2026

Actual local Streamlit server on loopback port 8503, Codex in-app browser tab 6. These were real chooser, dropdown, button and download actions, separate from AppTest. The temporary server was started without optional source-PDF bytes; their absence remains explicit. The user's existing port 8502 server was not restarted for this exercise.

## Established behavior

- Uploaded the actual 848-byte synthetic wide CSV; explicitly chose all eight columns and exact `done` completion value; confirmed synthetic draft scope.
- Preview existed before calculation. Ran the check and observed 1 PASS / 1 POTENTIAL_DEVIATION / 4 DATA_QUERY / 1 NOT_EVALUABLE.
- Downloaded ZIP, evidence JSON and review CSV using the actual UI controls. `verify_preparation_downloads.py` compares them against installed-CLI/shared-engine artifacts; all three are byte-identical to their respective expected outputs. The original source is exact inside the ZIP.
- Selected record 2. Original February 22 vaccination / March 4 call and the calculated February 29–March 3 inclusive window / one day outside were visible. Screenshots are retained.
- Changed actual-call mapping to the vaccination column: previous preview/result/downloads disappeared, scope unchecked and preparation disabled. Reconfirmation then preparation returned COLUMN_REUSED. Restoring the mapping allowed a fresh result.
- Cleared that source/result before replacement. A real 1,100,000-byte upload was rejected at the browser's 1MB cap. No old mapped output remained.
- A repository-local 10-byte malformed CSV reached the application and returned ROW_WIDTH, source record 1, without an old result/download.

## Failures preserved, not counted as passes

The first 9-byte malformed file (`wrong` newline `1,2`, outside the repository) failed upload transport with AxiosError: Network Error. Two retries, including one after reloading only the temporary test tab, also failed. A wait for the application's Clear button timed out because the file had never reached application parsing. Known-valid source upload subsequently worked. The repository-local malformed file with a final newline then reached the parser and produced the expected rejection.

Both file location and final newline differed in the successful attempt, so this review does **not** attribute a root cause or claim a transport fix. The browser console retains three upload errors. These do not become a clean-console claim. Python tests separately cover malformed CSV including missing final newline. No client security or upload protection was disabled.

[events.json](browser/events.json) records the sequence. [console.json](browser/console.json) preserves errors. [result.json](browser/result.json) verifies downloaded artifacts. [mapped-calculation.png](browser/mapped-calculation.png) shows original values and actual arithmetic. The final parser rejection is in [malformed-state.txt](browser/malformed-state.txt).

No new embedded-viewer, OS-print, public deployment, real participant or second-machine claim is made by this exercise.

The existing user-facing server at port 8502 was inspected separately. It showed a pending file-change rerun and no selected input files. Rerun displayed the new **Map one spreadsheet** first page; its screenshot and accessibility state are retained. The temporary tab 6 was closed and owned verification server 8503 was stopped after testing. Server 8502 remains available.
