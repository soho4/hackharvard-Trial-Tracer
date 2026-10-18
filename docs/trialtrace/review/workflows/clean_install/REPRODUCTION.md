# Workflow clean installation — 18 October 2026

A newly created `workflow_clean_env` installed the pinned UI/test dependencies
and a regular, noneditable wheel built from the final workflow source. The
installed probe ran with Python `-I` from outside the checkout. Every imported
`trialtrace` module came from this environment's `site-packages`; neither
`PYTHONPATH` nor a source-directory addition was used in the probe.

This passed on the same Mac with Python 3.13.4. It does not establish a
second-machine reproduction, human source review or clinical validation.

## Final app-only rerun

After the browser review, the app changed its empty intake display from
`st.json(None)` to explanatory captions. The core and locked dependencies did
not change. The same fresh installed environment reran the complete isolated
probe successfully without reinstalling either. The final app SHA-256 is
`1068c0d08a744acbeef751873641003e495540a33e0addde0ec3feeed1b4a9d6`;
the installed core remains `5c3a04fc876cd946228433b156bfc78912b8c342011154288fda619fa08451d9`.

The final result is `../clean_install_final/result.json`, with immutable run
`../clean_install_final/runs/20261018T091959.436186Z-73352535/` and command record
`../commands/20261018T091959.384898Z-workflow-final-app-isolated-probe-7564a048/`.
It repeats all CLI/upload equality, installed helper, comparison and AppTest
lifecycle assertions below, with zero app exceptions. The earlier result and
wheel remain intact in this folder. Use `--out` targeting `clean_install_final`
to keep a final-app probe separate from earlier evidence. AppTest still does
not establish browser rendering behavior; the actual browser review is separate.

## Verified results

- All environment, dependency, wheel, installation and probe commands exited 0.
- `pip check` reported no broken requirements. `result.json` records every
  installed dependency version, source-module hash and imported module path.
- The three actual CSV datasets under `examples/browser` produced exactly equal
  bytes through the installed upload adapter and independent installed CLI
  subprocesses: boundary PASS, outside POTENTIAL_DEVIATION at 1 day outside, and
  missing anchor DATA_QUERY with no calculation. Corrupt CSV was rejected with
  `INVALID_HEADER`.
- Installed intake inspection was ready without timing evaluation. Installed
  review lists contained respectively 0, 1 and 1 findings; the missing-anchor
  report retained its `MISSING_ANCHOR_ID` input issue. Saved-report loading and
  comparison found one unique matched visit with an actual PASS-to-potential-
  deviation change.
- The actual repository `app.py` ran through Streamlit AppTest against the
  installed core. Its five initial file slots were distinguished by label;
  only the three CSV roles were filled. Draft confirmation enabled execution,
  output bytes equaled the installed CLI, metrics were 1/0/0/0, and the review,
  input-issue and intake downloads were present. Clearing visits retired the
  old report/download and disabled execution. No app exception occurred.

AppTest is an in-process script check, **not a browser or network check**. The
parent review records actual browser runs separately. The probe emitted only
Streamlit's standard bare-mode context warning.

## Exact fingerprints

| Artifact | SHA-256 |
|---|---|
| Regular wheel | `6081984d49d4feaab0311a5fab209a5ef12daf4ef268cbb24244d2eab60ed48a` |
| Python core plus schema | `5c3a04fc876cd946228433b156bfc78912b8c342011154288fda619fa08451d9` |
| App | `a90a5695a105d5e89a45da41514f049726edaa3db7c1ab21c6e6f2c15c279f23` |
| UI dependency lock | `f284e9a44724f997950e91214a976dd342f3ff0cbe48160b3aedbfdb5319370e` |
| Public protocol bytes supplied | `da946b1ae23d40c41b332f1d0cb3311f0634e57009b4a37b9c6d6c60ee8bf186` |

The wheel is in `wheel/`; `wheel_manifest.json` also records the installed
distribution's archive hash. The probe result is in `result.json` and the
immutable run folder `runs/20261018T091057.699404Z-e5baf537/`, together with actual
CLI bytes, stdout, stderr and command records. The wheel contains the Python
core and schema. The app, viewer assets and registry snapshot are repository
files read during this app check. If source changes, rebuild and rerun; these
results cover the recorded fingerprints only.

## Reproduce

From the repository root, choose an absent sibling environment path:

```sh
trialtrace_repo="$PWD"
python3.13 -m venv ../workflow_clean_env
../workflow_clean_env/bin/python -m pip install -r requirements-ui.lock
../workflow_clean_env/bin/python -m pip wheel --no-build-isolation --no-deps --wheel-dir ../workflow_wheels .
../workflow_clean_env/bin/python -m pip install --no-deps ../workflow_wheels/trialtrace_core-0.1.0-py3-none-any.whl
../workflow_clean_env/bin/python -m pip check
cd ..
workflow_clean_env/bin/python -I "$trialtrace_repo/tools/check_g3_clean_install.py" \
  --repo "$trialtrace_repo" \
  --out "$trialtrace_repo/docs/trialtrace/review/workflows/clean_install"
```

For the exact executed source-byte configuration, append
`--source-pdf /path/to/Prot_000.pdf` using the public PDF with the fingerprint
above. Without it, the reports explicitly record source bytes as not supplied;
CLI/upload/app equivalence is still checked. The executed PDF path was
`work/source_check/.sources/Prot_000.pdf`, outside the repository.

Use `tools/record_command.py` to preserve each command's real exit status and
logs. Its record directories for this installation are under `../commands/`:

| Step | Record directory |
|---|---|
| Create absent environment | `20261018T090818.594049Z-workflow-create-fresh-venv-a0b5de2e` |
| Install pinned dependencies | `20261018T090831.588039Z-workflow-install-locked-dependencies-e18bff39` |
| Build wheel | `20261018T091040.267243Z-workflow-build-regular-wheel-efa99d7f` |
| Install wheel | `20261018T091044.980566Z-workflow-install-regular-wheel-e6b105ee` |
| Dependency check | `20261018T091057.648233Z-workflow-clean-pip-check-4c6e377a` |
| Isolated installed probe | `20261018T091057.648321Z-workflow-isolated-clean-probe-6476c069` |

## Intake and accounting regression evidence

The 46 initial inspection tests passed. A later review reproduced acceptance of
contradictory saved metadata: accounting claimed zero anchors while findings
still cited anchor records. Three failing cases were preserved in
`../commands/20261018T090929.257515Z-workflow-accounting-contradiction-reproduction-18e117d9/`.
The helper now rejects out-of-range cited ordinals and records simultaneously
cited and marked unused. It does not infer that an absent reference proves a
record unused. A subsequent test-only placement mistake produced three
`IndexError` failures; that run remains preserved as `090948` rather than being
reported as a product failure or discarded.

After correction, all **97 inspection and comparison tests** passed in
`../commands/20261018T091013.744822Z-workflow-accounting-consistency-final-307831cf/`.
These exercise actual parsed rows/engine bundles, malformed optional metadata,
multiple reasons on unreferenced invalid records, exact provenance, no timing
conclusions during intake, evidence amplification limits and spreadsheet-safe
derived CSV while canonical JSON values remain unchanged.
