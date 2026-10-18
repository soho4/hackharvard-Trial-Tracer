# Explicit spreadsheet preparation acceptance

The feature is a bounded wide-CSV adapter to the existing draft engine. The rule, source approval requirements, evidence schema, arithmetic and teammate viewer are unchanged. No runtime answer-file reads or fixture fallback were introduced.

| Requirement | Executed evidence |
|---|---|
| Explicit meanings and completion value, synthetic scope, no inferred dates/joins | Core preparation tests; component/UI choices and scope lifecycle; actual browser preview |
| Preserve source bytes, every logical row, unused columns and transformation lineage | Seven-row actual-file package; ZIP/source/generated/report hashes; browser-download equality |
| Bound malformed data and avoid silently normalizing it | UTF-8/BOM, quoting/newline/width/header/cell/column/row/byte tests; no trimming/coercion/dedup; actual ROW_WIDTH browser rejection |
| Genuine calculation and conservative uncertainty | Literal expected seven-row outcome list and hand-calculated leap-day interval; unknown values have no timing calculation; changed March 5 date gives two days outside |
| Incorrect assumptions should be detectable by external answers | Deliberately swapped date-column mapping failed frozen expected-status assertions, exit 1; wrong output retained under mutation/actual_run. This proves the challenge detects that error, not that the application understands arbitrary column semantics. |
| No stale results when mapping/scope/source changes | Component tests; browser mapping change, clear-before-oversize and malformed replacement |
| Shared engine and reproducible output | Installed isolated CLI byte parity; actual browser JSON/ZIP/review CSV parity; fresh regular-wheel environment outside source checkout |
| Existing workflows remain functional | Full suite: **447 passed in 13.84 seconds**, exit 0; isolated fresh-environment probe exercises old three-table and new mapped path |

The literal example expectations were authored before running this mapping exercise, not generated from its results. They are engineering oracles by the implementation agent, **not independent human adjudication**. Current application tests include the prior 424 plus 23 new preparation/parser/component cases. Historical viewer tests are separate, not added to that total.

Current core digest: `d20f8e50e3aafb80802847cef31bdee6b8c73b458bc0b718b413e3108426aebd`.
Current app digest: `1103ee12833069c2425652e2607735e74da00bbf1f7dd137fbf2a299269f24b5`.

- [Actual file acceptance](actual_run/result.json)
- [Fresh installation](clean_install/result.json): regular wheel, Python isolated mode, installed-module paths and exact source/dependency checks; same Mac only.
- [Browser review](BROWSER_REVIEW.md), including recovered upload errors and limits.
- [Command records](commands/): stdout/stderr, commands and exit codes, including intentional failure.
- [Technical gate](../../gates/PREPARATION_TECHNICAL.json).

These tests establish implementation behavior, not compatibility with a real vendor export, accurate rule applicability, clinical safety, reviewer usefulness or savings. Those require [the validation plan](../../PILOT_VALIDATION_PLAN.md).
