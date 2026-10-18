# Independent technical core review

This review inspected the v4 core and ran disposable probes without editing implementation, tests, the candidate rule, or teammate code. The implementation owner repaired the issues below. Red execution evidence remains preserved separately from the fix verification.

## Core findings and verified resolutions

| Finding | Actual red result | Verified resolution |
|---|---|---|
| P1: malformed known CLI option left stale output | After a valid run, a dangling `--anchors` returned exit 2 but left the previous success bytes at the output path. | The old report is preserved separately; malformed invocation returns structured diagnostics and leaves no success at the target. |
| P1: diagnostic cleanup occurred after publication | A diagnostic-path directory caused exit 2 with `success_bundle_written=false` despite a newly written success file. | Directory is refused before publication, retained unchanged, and an old valid output survives separately. |
| P1: case-insensitive input/output aliases | On this Mac, output `ANCHORS.CSV` moved the `anchors.csv` input. A visits input named `REPORT.JSON.DIAGNOSTICS.JSON` was deleted during a successful `report.json` run. | Filesystem identity checks refuse both aliases with `OUTPUT_INPUT_COLLISION`; all input hashes remain unchanged and no `.previous` directory is created. |
| P1: abbreviated input option bypassed cleanup reservations | `--anc <copy> --output <same-copy>` moved the input before evaluation. Disabling argparse abbreviations alone still moved it before rejecting the option. | Cleanup now conservatively reserves the possible input target while argparse rejects abbreviations. The exact repro returns `OUTPUT_INPUT_COLLISION`, preserves all input bytes, and creates no archive. |
| P2: lone surrogate in rule metadata escaped structured error handling | A UTF-8 rule containing an escaped lone surrogate in `interpretation_notes` caused `UnicodeEncodeError`, exit 1, traceback, and no diagnostic file. | Invalid Unicode configuration now returns exit 2 with structured diagnostics and no success bundle or traceback. |
| P2: unknown but consistently declared role passed semantic validation | Renaming `anchors.csv` and its evidence references to an arbitrary role was accepted. | The actual-engine bundle validator now rejects the unknown role. |

`probe_results.json`, `case_collision_results.json`, `abbrev_collision.json`, `abbrev_recheck.json`, and `surrogate_rule.stderr` preserve the observed failures. `fix_verification.json` records the successful regression assertions and unchanged source hashes before/after that run. `abbrev_fixed.json` records the exact final abbreviation-collision regression at `2026-10-18T07:35:56Z`, including before/after input hashes and CLI SHA-256 `cd7bd3322ca250a2c8171f9425100e6bf34e19a3bcbc4a316dd2599fdd63a823`.

No unresolved core bug remains among the material cases exercised in this review. This is bounded technical review, not a claim of exhaustive correctness or human source acceptance. The earlier G1 resource/cell-limit findings were independently reported and repaired; this review observed incremental evidence accounting and serialization in the core.

## Remaining teammate viewer compatibility defect

The teammate validator at `origin/abinet/evidence-viewer`, commit `1b216519e93866bca3fc36be174ec0f5bf05f793`, path `features/evidence_viewer/contract.js`, SHA-256 `e79299e71aa0a84f33299070af8cc596cf2a7740f9a71a3416b768ae3ae6ebc6`, rejects real calendar years 0001-0099 because its numeric JavaScript date construction maps those years into 1900-1999.

The probe produced actual core exports from newly written three-file synthetic inputs. Years 0001 and 0099 each computed PASS with January 8 as target/actual, January 8-11 as the inclusive interval, and zero days outside. The core schema/semantic checks and unchanged supplied reference validator accepted both exports. The teammate validator rejected all four calculation dates. Control years 0100 and 2026 passed all validators. Node process exit 0 alone was not treated as validation success; the returned `ok` field was checked.

`viewer_year_results.json` binds the actual generated bundles to final reviewed core source digest `58a1a80115a5409160529739efe27163a81af1d1184433a20900721e57a90a9f`, the teammate commit/hash, and the reference validator hash. The probe did not change calendar arithmetic, restrict valid dates, alter candidate semantics, or edit teammate files. Reference-contract CORE_EXPORT can pass; G3 integration should retain this teammate boundary defect as an explicit blocker until the viewer owner repairs and retests it.

## Packaging and provenance observations

A wheel built successfully from a separate package snapshot using ordinary build isolation. Inspection confirmed the Python modules, packaged evidence schema, declared jsonschema dependency, and CLI entry point. An earlier `--no-build-isolation` attempt failed because the review environment lacked the build backend; this was not classified as an application packaging failure. The wheel snapshot predates the final fixes and is not release or final-code reproduction evidence.

Generated core metadata consistently remained draft, synthetic, pending human source review, and not clinically validated. Reports bind actual rule/input/source-code digests and preserve the PDF hash as null when bytes were not supplied. No clean-commit or source-identity claim was inferred from those fingerprints.

## Reproduction and retained materials

Probe scripts were executed from `work/review_core` with the repository at sibling `work/TrialTrace`; archived copies retain those assumptions. They write only disposable scratch inputs and reports. The copied review evidence contains synthetic failure records, probe scripts, and boundary-test exports. No PDF, PDF rendering, source-text excerpt, virtual environment, package snapshot, wheel, or teammate source file is included in the repository review directory.
