# Core acceptance matrix — v4 engineering contract

These are specifications to implement and execute, not results already observed in the new application. The source interpretation remains pending. No fixed minimum test count replaces the behaviors below.

## Scope and prerequisite labels

The first session ends at CORE_EXPORT, not a website. G1_TECHNICAL can advance while G0_SOURCE is pending. G2/CORE_EXPORT may demonstrate explicit DRAFT_ENGINEERING only; accepted source claims remain blocked. Use the unchanged A10_DRAFT_2 rule file, not the old symmetric ±2/±4 rulebook or the old lab detector.

Draft fixtures contain `DRAFT_SYNTHETIC` mappings except H09, which is deliberately `UNRESOLVED`. This new input-only value is an explicit v4 clarification. It is not proof of review and must be refused as reviewed scope in normal reviewed mode. No teammate output-schema change is needed.

## Frozen hand cases

`fixtures/core_draft/expected.json` binds these drafted engineering expectations to the candidate rule hash. A normal reviewed-mode invocation without actual acceptance must not compute accepted-source findings from these files. An explicit draft-mode invocation exercises actual parsing/joining and calculation under pending assumptions.

| ID | Input distinction | Expected under draft mode |
|---|---|---|
| H01 | May 1 vaccination, May 8 safety call | PASS; interval May 8–11; 0 outside. |
| H02 | Same starting date, May 11 call | PASS at upper bound. |
| H03 | Same starting date, May 12 call | POTENTIAL_DEVIATION; 1 day outside. |
| H04 | Same starting date, May 7 call | POTENTIAL_DEVIATION; 1 day outside. |
| H05 | Missing actual vaccination date | DATA_QUERY; null calculation. |
| H06 | Decision date May 1 is irrelevant; actual vaccination May 3; call May 10 | PASS; interval May 10–13, not May 8–11. |
| H07 | Clinic event, not safety phone call | NOT_EVALUABLE; no date calculation even though timing looks plausible. |
| H08 | Referenced anchor belongs to another participant | DATA_QUERY before arithmetic. |
| H09 | Unresolved cohort assignment | NOT_EVALUABLE. |
| H10 | Feb 22, 2028 vaccination; Feb 29 call | PASS; interval Feb 29–Mar 3. |

Expected totals for this supplied draft file: 10 visits, 4 PASS, 2 POTENTIAL_DEVIATION, 2 DATA_QUERY, 2 NOT_EVALUABLE. These are case expectations, not current executed outputs or an accuracy claim. The future engine must calculate rather than read expected.json.

## Required additional cases before each technical promotion

| ID | Check | Required observed behavior |
|---|---|---|
| P01 | Missing/extra/duplicate headers | Structural error, no success bundle. |
| P02 | Header order changed | Accepted; field mapping is by name. |
| P03 | LF, CRLF, quoted commas/multiline cells | Valid standard CSV parses; raw rows and logical ordinals preserved. |
| P04 | Leading UTF-8 BOM | Accepted under documented policy; raw-byte hash includes BOM. |
| P05 | Invalid UTF-8, NUL, malformed quoting, wrong row width | Structural error, not partial silent success. |
| P06 | Empty byte stream / whitespace-only file | Structural error. |
| P07 | Header-only visits table | Valid empty result plus input accounting; zero findings is not “all patients compliant.” |
| P08 | Header-only anchors with present visits | Affected visits query missing relationships. |
| P09 | Limit +1 byte/row/cell | Explicit size-limit error; no silent truncation. |
| I01 | Empty ID or leading/trailing whitespace in ID | Query with safe unique source identity; do not normalize silently. |
| I02 | Duplicate key with identical or conflicting rows | Preserve conflict and query dependent records; no first/last wins. |
| I03 | Wrong study, participant or site in join | Query; no cross-identity evidence arithmetic. |
| I04 | Missing anchor or assignment | Query, with original visit evidence; do not invent a missing row. |
| I05 | Bad unreferenced anchor/assignment | Appears in input diagnostics; counts account for it. |
| I06 | Unknown event or anchor kind | NOT_EVALUABLE, not clinical pass. |
| I07 | Unsupported version, code or schedule | NOT_EVALUABLE; never silently select a latest rule. |
| I08 | `DEMO_REVIEWED` supplied without actual global review | NOT_EVALUABLE; a CSV label cannot approve the source. |
| I09 | DRAFT_SYNTHETIC in reviewed mode | Refused as reviewed applicability; no automatic promotion. |
| I10 | UNKNOWN status with a populated date | DATA_QUERY for completion evidence, not a confident date result. |
| D01 | Exact date shape and validity | Reject compact dates, ambiguous locale dates, nonexistent dates and timestamps as row queries. |
| D02 | Derivation at representable date bounds | Overflow handled as a query with null calculation, not a whole-process traceback. |
| D03 | Actual date on each endpoint and just outside | Assert target, both bounds, outside days and correct category. |
| D04 | Shift valid anchor and actual by same days | Category/outside distance unchanged; evidence dates and input hashes change. |
| D05 | Synthetic generalized asymmetric/zero-width rule unit test | Validate supported math without claiming additional clinical rules were approved. |
| C01 | Negative upper tolerance, positive lower tolerance, bool as int, unknown units/bounds/policy | Configuration error; do not produce a clinical-style result. |
| C02 | Change source locator/rule bytes | New rule hash and corresponding evidence; prior acceptance no longer binds automatically. |
| E01 | Raw file changed but parsed values equal, such as line endings | Raw input hash changes; semantic counts may remain the same. |
| E02 | Duplicate/missing visit IDs | Still unique finding IDs, with no overwritten evaluations. |
| E03 | Evidence file hash mismatch / missing declaration | Export validation fails before publication. |
| E04 | Schema-valid but duplicate finding IDs | Additional semantic validation rejects. |
| E05 | Outcome/calculation/null/date inconsistency | Semantic validation rejects. |
| E06 | Same raw inputs/config/mode/code | Stable content identity and ordered results; volatile fields explicitly separated. |
| E07 | Export >2,000,000 bytes | Explicit failure, no silently shortened evidence or reports the viewer cannot open. |
| E08 | Safe original JSON export | No fabricated metadata; numeric/count values come from current computation. |
| X01 | Valid run followed by corrupt run to same output target | Failed new run does not leave old success output at the target as the new report. Keep old runs separately. |
| X02 | New never-bundled identifiers/dates via actual CLI files | Results reflect those bytes, not fixture ID matching. |
| X03 | Controlled boundary mutation in temporary implementation copy | Assertions about behavior fail; syntax/import errors do not count. |
| X04 | Reviewed-mode request while G0 pending | Explicit blocker and nonzero CLI exit; do not auto-switch to draft mode. |
| X05 | Runtime attempts to read expected labels | Prohibited; test harness uses the answer key, not application code. |

Test all source rows are accounted for independently of how many visit findings exist. A diagnostics collection may include unused anchors/assignments without incorrectly inflating the number of evaluated visits.

## Actual integration commands to implement, not preexisting executables

Expose a documented CLI with this behavior (adapt module path once to existing layout):

```bash
python -m trialtrace.cli \
  --anchors path/to/anchors.csv \
  --visits path/to/visits.csv \
  --assignments path/to/assignments.csv \
  --rule rules/candidate_rule.json \
  --draft-synthetic \
  --output path/to/actual_bundle.json
```

It must read these actual files. An unknown flag fails instead of being ignored. Configuration or file-level failure returns nonzero and writes diagnostics separately; row queries may coexist with valid findings in a successful structured report. Do not state this command exists until implemented and executed.

Validate actual output against `contracts/evidence_bundle.schema.json` with a real validator, plus semantic checks. The reference JavaScript `validateBundle` can additionally check compatibility with the supplied viewer reference. Its green result does not authenticate source data or show the teammate's new implementation works.

## Required evidence per unit

G1: test log, importer CLI result on novel files, corrupt-input refusal, row accounting, raw hashes and ordinals.

G2: hand-case comparison, new-file computation, all uncertainty branches, source/config sensitivity, meaningful mutation failure, exact code/rule/input state.

CORE_EXPORT: actual computed bundle, schema/semantic/viewer-reference results, determinism comparison, stale-output failure case, code and Git status, hand-back with remaining source and browser blockers.

The implementation agent may write extra tests before adding behavior. Frozen expected values cannot be changed just to match output. Separate review can identify a real specification error; preserve it, version the decision and obtain approval rather than burying it in a passing test change.
