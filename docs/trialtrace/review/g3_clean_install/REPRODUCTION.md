# G3 clean installation — 18 October 2026

A new virtual environment installed the fully pinned UI/test dependencies and a
regular wheel built from the current package. The installed core was exercised
with Python isolated mode from outside the checkout. This succeeded on this same
Mac using Python 3.13.4; it is not evidence of a second-machine reproduction.

## Results

All installation commands and the probe exited zero. `pip check` reported no
broken requirements. `result.json` records every installed dependency version,
the exact package and app fingerprints, original input hashes, commands and
results. Every imported `trialtrace` module came from the fresh environment's
`site-packages`, with no source-directory addition to `sys.path` or `PYTHONPATH`
shortcut. The project was installed as a wheel, not editable.

Three actual browser-input datasets were executed through both the installed
upload adapter and separate installed CLI subprocesses. Their output bytes
matched exactly:

| Case | Literal expected observation | Actual |
|---|---|---|
| Boundary | Anchor 2040-02-22, target 2040-02-29, last allowed date 2040-03-03; call 2040-03-03 passes | PASS, 0 days outside |
| Outside | Same window, call 2040-03-04 | POTENTIAL_DEVIATION, 1 day outside |
| Missing anchor | No confident timing calculation | DATA_QUERY, null calculation |

The corrupt-file case was rejected with `INVALID_HEADER`. No sample fallback was
used. The existing public protocol PDF bytes were hashed for these runs; this
does not establish human source approval.

The actual `app.py` also executed through Streamlit AppTest in the clean
environment. It accepted three actual file uploads, required draft confirmation,
ran the check, and returned bytes identical to the installed CLI. Its counts were
1 PASS and 0 in the other categories. Clearing the visits slot removed the
report/download and disabled the run button. There were no app exceptions.
AppTest executes the app script in-process; it is **not** a browser/network test.
The actual browser evidence is recorded separately.

AppTest emitted its standard bare-mode context warning. The first run also
warned that `components.v1.html` is deprecated. The integrator changed the app to
the installed version's `st.iframe` API, then the complete installed probe was
rerun successfully. The final run has no deprecation warning; both command
records remain preserved.

## Exact artifacts

- Wheel: `wheel/trialtrace_core-0.1.0-py3-none-any.whl`
- Wheel SHA-256: `5fc205f57901a03b8cca51b902d7d457da1ac85764340c026dfcbda9433b6e80`
- Package/schema SHA-256: `eb7350f8c7adef275604cfc03b2c27fe8d1c0dd0b4a794f9bf39e41bbc80ebc2`
- Final app SHA-256: `6ab33e3e3f7253b16e2226ab4037fba904e958b9f2ced15de18d34cb9f092a9e`
- UI lock SHA-256: `f284e9a44724f997950e91214a976dd342f3ff0cbe48160b3aedbfdb5319370e`

The detailed result is bound to those exact files. If the app/core changes,
rebuild the wheel if needed and rerun the probe; old results do not cover new code.
The app, rule, viewer assets and public-metadata snapshot are repository files;
the wheel packages the Python core/schema. The app smoke test reads the actual
repository script while importing its core from the installed wheel.

## Reproduce from a checkout

Use an absent sibling path for the fresh environment. On this machine the base
interpreter was `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`.
The commands below assume an available Python 3.13 executable and a Unix shell:

```sh
trialtrace_repo="$PWD"
python3.13 -m venv ../g3_clean_env
../g3_clean_env/bin/python -m pip install -r requirements-ui.lock
../g3_clean_env/bin/python -m pip wheel --no-build-isolation --no-deps --wheel-dir ../g3_wheels .
../g3_clean_env/bin/python -m pip install --no-deps ../g3_wheels/trialtrace_core-0.1.0-py3-none-any.whl
../g3_clean_env/bin/python -m pip check
cd ..
g3_clean_env/bin/python -I "$trialtrace_repo/tools/check_g3_clean_install.py" --repo "$trialtrace_repo"
```

For the same source-byte provenance as the executed review, append
`--source-pdf /path/to/Prot_000.pdf` using the already retrieved original public
PDF (SHA-256 `da946b1ae23d40c41b332f1d0cb3311f0634e57009b4a37b9c6d6c60ee8bf186`).
Without that optional argument, the report honestly says source bytes were not
supplied; adapter/CLI/app equivalence is still checked for that configuration.

The probe creates a uniquely named `runs/` record and updates `result.json` after
all assertions succeed. Subprocess output, exit codes and hashes are preserved.
No clinical validation, reviewed-product promotion, or deployment is claimed.

## Command records

| Command | Record directory |
|---|---|
| Create fresh environment | `commands/20261018T083532.118281Z-create-fresh-ui-venv-ba372b48/` |
| Install locked dependencies | `commands/20261018T083552.563069Z-install-locked-ui-dependencies-a477910a/` |
| Build regular wheel | `commands/20261018T083724.482993Z-build-regular-core-wheel-a36f4134/` |
| Install regular wheel | `commands/20261018T083746.636274Z-install-regular-core-wheel-846526e5/` |
| Check dependencies | `commands/20261018T083747.109553Z-clean-pip-check-2bb1f671/` |
| Isolated installed probe | `commands/20261018T083747.109133Z-isolated-installed-g3-probe-daa39890/` |
| Final installed probe after iframe API update | `commands/20261018T084318.056381Z-isolated-final-iframe-app-probe-1b9c48af/` |
