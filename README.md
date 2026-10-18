# TrialTrace core — draft synthetic demonstration

TrialTrace reads three actual CSV files, checks their identities and relationships,
and applies one deterministic timing rule to explicitly mapped synthetic visits.
It exports the original evidence and uncertain cases in the existing viewer format.

**Source interpretation is pending independent human review. Clinical validation is
false. Only explicit `DRAFT_ENGINEERING` execution is enabled.** A potential deviation
is a flag for human review; PASS covers only this timing check. No patient data is accepted.

The public example protocol is Moderna's NCT04470427 / mRNA-1273-P301 amendment 10,
[Table 21](https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf).
It is not Regeneron data. All operational CSV examples here are newly authored synthetic records.

## Install and run

Python 3.11 or later is required. Python 3.13.4 was tested. Use a regular package
installation; the tested dependency versions, including the build backend, are pinned.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps .
.venv/bin/python -m trialtrace.cli \
  --anchors examples/novel/anchors.csv \
  --visits examples/novel/visits.csv \
  --assignments examples/novel/assignments.csv \
  --rule rules/candidate_rule.json \
  --draft-synthetic \
  --output run.json
```

The example calculates target 2032-01-03, inclusive window January 3–6, and PASS
for a January 6 call. Substitute `examples/novel/visits_changed.csv`: the January 7
call produces POTENTIAL_DEVIATION, one day outside. The runtime never reads an answer key.

An optional `--source-pdf /path/to/Prot_000.pdf` records that file's exact hash.
The runtime labels this as local bytes hashed, without claiming identity validation
or human review. Without the option, the source hash is null. Technical acquisition
and identity evidence for this session is recorded separately in `docs/trialtrace/source_check/`.

Omitting `--draft-synthetic` fails closed. `DEMO_REVIEWED` in an assignment CSV cannot
authorize a reviewed run. No human approval record was created.

## Input and failure behavior

The CLI assigns the three logical roles; external filenames may vary. Headers are
exact but may be reordered. UTF-8 with optional recorded BOM, commas, standard CSV
quoting, and LF/CRLF are supported. No IDs or dates are silently repaired.

- `anchors.csv`: `study_id,participant_id,site_id,anchor_id,anchor_code,anchor_kind,anchor_date`
- `visits.csv`: `study_id,participant_id,site_id,visit_id,visit_code,event_kind,actual_date,visit_status,anchor_id,assignment_id`
- `assignments.csv`: `assignment_id,study_id,participant_id,site_id,rule_version,schedule_code,mapping_status,mapping_note`

Each table is limited to 1,000,000 bytes, 500 records and 10,000 characters per cell.
Rule JSON is limited to 65,536 bytes. Export is limited to 2,000,000 bytes; excessive
evidence causes an explicit failure, never truncation.

Every structurally valid visit produces one outcome. Broken identity/date/relationship
evidence becomes DATA_QUERY; unsupported kinds or unresolved scope become NOT_EVALUABLE.
Both have null calculations. Duplicates remain ambiguous even when identical. Invalid
unused anchors and assignments appear in `input_accounting`. No missing-event inference
or count of “clean patients” is made.

Structural/configuration errors exit 2 and write `<output>.diagnostics.json` when that
path is usable, plus structured stderr. Previous reports move to a uniquely named
`.previous/` file before a new run. Output/input collisions are refused without altering
inputs, including case aliases and hard links. A filesystem that denies writes can
prevent cleanup; such errors are reported rather than labeled successful.

## Verification and boundaries

```sh
.venv/bin/python -m pytest tests -q
.venv/bin/python tools/check_mutation.py
.venv/bin/python tools/run_acceptance.py
node tools/check_viewers.cjs
```

The recorded application suite has 236 passing tests. The deliberate upper-bound
mutation causes five mathematical assertion failures. Saved real input/output evidence
is in `examples/execution/`; command logs, failures and exit codes are in
`docs/trialtrace/commands/`. Node is used only for optional viewer compatibility checks.

Outputs contain exact raw-file hashes, source rows and logical ordinals, rule-byte
hashes, unique source-derived finding IDs, and a digest of the actual package source
and schema. Canonical JSON is UTF-8 with sorted keys, compact separators and one final
newline. There are no volatile timestamps in bundle content, so identical inputs,
configuration and code produce identical output bytes.

Both isolated viewer validators accept the eight saved normal-date reports. The
teammate validator has a documented valid-year 0001–0099 defect; the core and unchanged
handoff reference validator accept these dates. Fix and retest that integration in G3.
The teammate branch was not merged or modified.

There is no main upload UI, browser integration, deployment, clinical validation or
reviewed-mode promotion in this first session. A fresh local venv/wheel reproduction
was tested; another machine was not. See [HAND_BACK](docs/trialtrace/HAND_BACK.md) for
gate state, commits, pending source review and the next action.
