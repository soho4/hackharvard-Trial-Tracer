# Decisions

- User explicitly identified existing GitHub repository; clone is work/TrialTrace. Main was clean with only README and ignore file. No repository AGENTS instructions existed. New feature branch codex/trialtrace-core-v4. Separate origin/abinet/evidence-viewer branch is preserved and not merged.
- Python src package, pytest, jsonschema; no runtime model, frontend, database or service.
- Retain exact candidate/schema/fixtures. Source review remains pending. Reviewed execution fails closed; explicit draft CLI mode is required.
- Requirement and expected outcomes are frozen in CORE_ACCEPTANCE.md before implementation; separate test author owns application tests.
- Canonical JSON: UTF-8, sorted keys, compact separators, ensure_ascii=False, allow_nan=False, final newline. No generated timestamp in result content.

- First session supports explicit draft execution only. Reviewed mode always fails closed; CSV DEMO_REVIEWED never substitutes for source approval. Future reviewed-mode enabling needs real review/acceptance and tests.
- Rule JSON limit: 65,536 bytes, duplicate keys/unsupported fields/unencodable Unicode rejected.
- Preserve previous output before failures. Protect inputs by filesystem identity (case aliases and hard links). Reserve possible abbreviated inputs during cleanup without accepting those flags.
- Count evidence size before duplicate expansion, then incrementally enforce 2,000,000 exported bytes without truncation.
- Code digest includes package Python sources and exact packaged schema. Canonical output has no timestamps. Run ID hashes complete content before run_id; finding IDs bind domain tag, role/raw-hash snapshot, rule digest, mode and ordinal.
- Mac marked editable-install .pth hidden; later direct imports failed. Preserve those logs. Regular wheel installation succeeds and is the documented installation mode.
- Optional --source-pdf only hashes local PDF bytes; source identity inspection remains separate logged evidence.
- Original curl telemetry with local network details stays outside public commits; original logs remain locally preserved.

## 18 October 2026: authorized local UI continuation

- The user's direct request to review, build, iterate, launch and check real behavior
  authorizes the local G3 draft continuation after the core hand-back. It does not
  supply human source approval. G0 and reviewed-product promotion remain blocked.
- Use actual public protocol bytes and a dated ClinicalTrials.gov metadata snapshot.
  That response has aggregate results, not matching participant event dates. Newly
  authored synthetic operational files test computation; do not portray them as patients.
- Add a byte-based upload adapter around the existing parser/engine/exporter. The
  CLI and app share these functions and PDF hashing; no alternate UI calculation.
- Bind the server to loopback, disable usage telemetry, and add a pinned UI environment.
  No database, runtime model, registry polling, or public hosting was added.
- Preserve accepted upload bytes in an explicit selected-file slot. Clear retires
  the report before the replacement chooser opens. This addresses Streamlit's
  client-side oversize rejection, which does not trigger the Python callback.
  A first disabled-widget attempt failed and was replaced, with evidence retained.
- Give filtered finding selections an identity derived from the available IDs so
  the visible label cannot remain attached to an old selected finding.
- Import the teammate viewer at commit 1b216519e93866bca3fc36be174ec0f5bf05f793.
  Keep schema/fixtures unchanged and limit fixes to early-year parsing and wrapping
  long engine IDs. Preserve the upstream snapshot and both red/green results.
- Use the installed Streamlit st.iframe API for the trusted local viewer assets.
  Actual Chrome upload/download works. The in-app browser's missing iframe download
  event remains a documented platform observation, not a claimed fix.
- Technical AI challenges and fresh same-machine installation improve engineering
  confidence; they do not satisfy independent human source review or a real-data pilot.
