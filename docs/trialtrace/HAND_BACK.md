# TrialTrace core hand-back — draft engineering

The three-table importer, deterministic timing engine and compatible evidence export
are implemented and executable. **G1_TECHNICAL, G2_TECHNICAL and CORE_EXPORT passed
their technical checks in DRAFT_ENGINEERING mode. G0 remains blocked.** No human
approval, clinical validation, frontend, merge or deployment is claimed.

## Execute now

Follow the regular-package installation in the root README, then run:

```sh
.venv/bin/python -m trialtrace.cli \
  --anchors examples/novel/anchors.csv \
  --visits examples/novel/visits.csv \
  --assignments examples/novel/assignments.csv \
  --rule rules/candidate_rule.json \
  --draft-synthetic --output run.json
```

The saved current-code demonstrations are under `examples/execution/`. Inputs are
real synthetic CSV files, and outputs came from the installed CLI without mocks or
answer-key reads. `before/bundle.json` is PASS for actual date 2032-01-06; changing
only that date to 2032-01-07 in `after/visits.csv` produces POTENTIAL_DEVIATION with
one day outside the inclusive January 3–6 interval. Each contains the source rows,
logical ordinals and actual hashes. Source bytes were supplied to these saved runs
for hashing; the example command above leaves that optional source hash null.

Missing and wrong-person anchors produce DATA_QUERY. Unresolved mapping and unknown
event produce NOT_EVALUABLE, all with null calculation. Empty visits produce zero
evaluations with accounting. A valid run followed by malformed CSV exits 2, removes
the success from the requested target, writes diagnostics, and preserves prior bytes
separately (`corrupt_replacement/previous_accepted.json`).

## Verification and evidence

- Current application suite: **236 passed**, no skipped tests. Includes exact input
  and output limits, CSV/UTF-8 failures, identities/joins/duplicates, missing evidence,
  date shapes/leap days/overflow, inclusive boundaries, configuration refusal,
  byte-sensitive provenance, semantic corruption, stable output and real subprocess CLI.
- Ten frozen draft cases: 4 PASS, 2 POTENTIAL_DEVIATION, 2 DATA_QUERY, 2 NOT_EVALUABLE.
  These are pre-authored engineering expectations, not clinical accuracy measurements.
- Mutation: changing the upper bound to `upper_days + 1` in an isolated code copy
  caused **five mathematical assertion failures**, subprocess exit 1. The harness
  exited 0 only after confirming that failure and unchanged original source.
- JSON Schema and semantic validation reject duplicate finding IDs, undeclared or
  inconsistent evidence hashes, unknown engine roles, invalid dates and inconsistent
  calculations. Both viewer validator snapshots accepted **eight actual reports**;
  duplicate-ID/hash-mismatch negative controls were rejected.
- A fresh local venv and wheel, run with Python `-I` outside the checkout, contained
  the exact schema and source digest and reproduced the CLI report byte-for-byte.
  This is same-machine reproduction, not an installation tested elsewhere.
- Technical review found and repaired evidence amplification, cell-limit diagnostics,
  stale-output/diagnostics failures, Unicode configuration errors, abbreviated flags,
  and case/hardlink input collisions. Earlier failing logs are preserved alongside
  passing regression evidence. AI technical review is not human source review.

Read `acceptance_results.json`, `viewer_compatibility.json`, `clean_install.json`,
`mutation/result.json`, `review/core/REVIEW.md`, `gates/`, and `commands/` for exact
commands, timestamps, stdout/stderr, exit codes, digests and expected/observed results.
`requirements-dev.lock` records installed dependencies; Python 3.13.4 and the bundled
Node runtime were used. Node is not needed to calculate dates.

## Repository and source changes

Verified origin: `https://github.com/soho4/hackharvard-Trial-Tracer`.
Dedicated branch: `codex/trialtrace-core-v4`.

- G1 checkpoint `22819663b5b12f9d32d90f45e8edba30a171cd13`: pushed; remote SHA verified.
- Implementation checkpoint `36660aa35b5a8684b4145b5f169a4b9c976bf9d5`: pushed; remote SHA verified.
- Code/schema digest: `58a1a80115a5409160529739efe27163a81af1d1184433a20900721e57a90a9f`.

The final documentation/evidence checkpoint follows the implementation checkpoint.
The delivered hand-back copy and delivery manifest record that exact final HEAD and
post-push verification; a commit cannot embed its own hash. No default-branch merge,
force-push, visibility change or public deployment was performed.

`src/trialtrace/` contains importer, relationships, engine, exporter and CLI modules.
`tests/` contains the independent behavior assertions; `tools/` contains evidence,
mutation, acceptance and compatibility checks. The contract, candidate and frozen
fixtures retain their original bytes. Project instructions were added because main
had none. Original personal/history material, PDF/renderings, credentials, virtual
environments and raw curl network telemetry were excluded from commits.

The teammate branch `abinet/evidence-viewer` was preserved. Its schema and six
fixtures exactly match the handoff. Only isolated validator snapshots were used for
compatibility checks; no frontend was built or changed.

## Pending review and limits

Technical source acquisition succeeded: original PDF, 2,728,675 bytes, 193 pages,
SHA-256 `da946b1ae23d40c41b332f1d0cb3311f0634e57009b4a37b9c6d6c60ee8bf186`.
The unchanged verifier passed eight identity/context checks; cover and relevant pages
were rendered and inspected by an agent. Source logs include initial dependency/TLS
failures and the successful native-curl acquisition without a TLS bypass.

Candidate hash: `f36336df90a1793a80b92f48ce273488a091547110856bdcc602587ddad9e7f0`.
No reviewer identity, approval checkbox or signature was completed. A real reviewer
must independently check cohort, safety-phone-call meaning, actual vaccination
anchor, zero early allowance, inclusive endpoints and hand cases. Also reconcile the
displayed note-number discrepancy: page 152 labels 4–11 while table superscripts are
1–8. Read the original [public protocol](https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf),
not only this summary. Local source-byte location is in `source_check/source_check_manifest.json`.

Reviewed execution deliberately fails closed. An approved-mode enabling mechanism
is not delivered by this first session; a CSV label cannot unlock it.

**Known separate viewer defect:** the teammate validator rejects valid years
0001–0099 because of JavaScript `Date.UTC` year remapping. Core arithmetic and the
unchanged reference validator accept those dates; years 0100 and 2026 also passed
the teammate probes. This is a G3 integration blocker, documented in
`review/core/viewer_year_results.json`. No bounds, candidate meaning or core output
was changed to conceal it.

There was no main UI/browser test, independent human source review, another-machine
installation, deployment or clinical validation. This bounded session stops at the
draft core export; no continuing background work is scheduled.

## Smallest next action

Review this core evidence and have an independent teammate review the exact protocol
and candidate hashes. Record a real decision without editing the immutable candidate.
Then explicitly authorize the next session; resolve the viewer year defect and test
the real upload/export flow before promoting any G3 claim.
