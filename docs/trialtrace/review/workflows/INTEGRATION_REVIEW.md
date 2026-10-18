# Workflow integration review

No new actionable defect found in the reviewed integration. This is an AI technical review of synthetic-data behavior, not human protocol approval or browser acceptance.

Reviewed `app.py`, `inspection.py`, comparison integration, and the newly authored workflow CSVs. Main-input and comparison slots both require explicit clearing before replacement; their callbacks invalidate the corresponding results and downloads. Intake diagnostics are recomputed from current uploads. Finding and input-issue CSVs are generated from the full bundle before display filtering, preserving complete review lists. Comparison displays substantive changes separately from provenance-only changes, exposes context differences, and retains canonical duplicate visit keys as unpaired groups.

A read-only AppTest probe passed against app SHA-256 `0a07bbd18a60ff64961c5d9b0577f421abd74afe36043b378f8a204a5ed5cd3d`: one valid upload exposed current intake only; a malformed second upload produced its own rejection while the third role remained missing; no result, evidence download, or review-list downloads appeared; clearing the malformed upload removed its error and retained the other selected bytes. This checks component state, not a browser's upload transport.

Joint shared-validator tests passed: `python -m pytest tests/test_comparison.py tests/test_inspection.py -q` returned exit 0, **94 passed in 0.42s**. Optional accounting is structurally validated when present. Absent accounting remains unknown rather than an asserted zero record count; legacy reports are not used to populate the current-run input-issue panel. An empty finding list does not create compliance claims.

## Independent literal expectation check

The following conclusions were checked from the CSV content and calendar reasoning, without calling the evaluator to derive expected answers:

- February 22, 2028 plus seven days is February 29; the inclusive latest date is March 3. V1 on March 3 passes; March 4 is one day late.
- December 25, 2028 plus seven days is January 1, 2029, with latest January 4. V2 on January 2 passes.
- V3 lacks its named anchor, V4 has an unsupported event kind, and both V5 rows share a duplicate canonical visit key. Thus before counts are PASS 2 / potential deviation 0 / data query 3 / not evaluable 1; after counts are 1 / 1 / 3 / 1.
- Four unique records can match; only V1 changes substantive values. Three other matched records change only file provenance. Both duplicate rows remain unpaired on each side, with no added/removed records.
- The seven input issues are: invalid unused anchor date (1), missing visit anchor (1), unsupported visit kind (1), duplicate visit rows (2), and unresolved plus undocumented unused assignment (2). Three issues belong to unused records.
- Non-PASS review-list counts are 4 before and 5 after. `=SYNTH-FORMULA` remains exact in JSON; the derived CSV must prefix it with an apostrophe.

These observations agree with `examples/workflows/expected.json`. No expected values or original evidence were edited during this review.
