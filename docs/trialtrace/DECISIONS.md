# Decisions

- User explicitly identified existing GitHub repository; clone is work/TrialTrace. Main was clean with only README and ignore file. No repository AGENTS instructions existed. New feature branch codex/trialtrace-core-v4. Separate origin/abinet/evidence-viewer branch is preserved and not merged.
- Initial core selection: Python src package, pytest, jsonschema; no runtime model, frontend, database or service in that first session.
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

## 18 October 2026: authorized local workflow continuation

- Add intake, findings/input-issue exports and saved-report comparison within the
  existing synthetic draft scope. The candidate rule, arithmetic, outcome meanings,
  viewer contract and human-review requirements are unchanged.
- Use the shared parser for preflight. Expose missing/rejected roles, byte and
  record counts, relationship/accounting information and a downloadable intake
  report before calculation. Structural readability is not a PASS outcome and
  does not bypass explicit synthetic draft opt-in.
- Keep **Findings to review** and **Input rows to review** separate. The latter
  includes unused invalid/conflicting rows and counts issues, not participants.
  Suggestions request evidence inspection; they do not resolve clinical findings.
  Display filters never narrow these full exports or canonical report bytes.
- Escape formula-like cells in derived spreadsheet CSVs and disclose that behavior.
  Keep exact values in evidence JSON, including deliberately adversarial synthetic
  identifiers. Put readable outcome/identity/reason/action fields first in the UI;
  retain exact run, finding and source references in exports/details.
- Compare saved reports without rerunning the engine or mutating either input.
  Require complete, unique identities and reject ambiguous canonical visit keys,
  even if duplicate rows name different participants/sites. Keep changed values,
  evidence fingerprints and rule/source/producer context distinct. Neither
  disappearance nor a status transition establishes missed activity, resolution
  or clinical improvement.
- Treat saved reports as untrusted bounded JSON. Validate optional accounting
  before accessing it, including consistency with evidence actually present in
  findings. Missing optional accounting remains unavailable, not zero issues.
- Apply Clear-before-replacement to both comparison slots. Current CSV checking
  and saved comparison have independent state; **Start a new check** resets the
  current CSV workflow, filters and draft opt-in without discarding saved comparison.
- Treat registry metadata as optional display context. A strict 100,000-byte
  loader rejects malformed/invalid declared metadata; the UI reports unavailability
  without invented facts or blocking an otherwise valid pinned draft rule.
- Reproduce current workflows through actual installed CLI output and a fresh
  regular wheel. Preserve earlier failures and their original source fingerprints.
  Keep component/CLI results separate from the final served-browser record for
  the added workflows. Report evidence/CSV byte equality separately from comparison
  JSON content equality. Preserve recovered tool/upload failures; the embedded
  saved-viewer chooser timeout does not become a new viewer pass. No human source
  approval or public deployment is added.
- Render unavailable preflight summaries as an explanation, not JSON null. Verify
  the display repair and optional-metadata failure path in the served browser;
  restore exact metadata bytes after deliberate fault injection and use a separate
  normal-state full-suite run for the final result.

## 18 October 2026: research and explicit spreadsheet preparation

- Follow the user's direct continuation with a source-preserving wide CSV path. One row must already contain the actual call and vaccination references; eight column meanings and exact completed-call value are explicit. Do not infer cross-row joins, dates, eligibility or applicability.
- Generate the three existing input tables internally, retaining every row and declaring fixed candidate context as synthetic user input. Repeated anchors remain queries, not silently deduplicated records. Preserve exact candidate/schema/viewer files.
- Keep original bytes and unused columns in the complete ZIP alongside chosen mapping, constants, lineage, generated table hashes and evidence JSON. The unchanged JSON schema refers to generated tables; never describe that alone as upstream source preservation.
- Research shows existing EDC rules and heterogeneous exports. Treat portable evidence review as a hypothesis; no vendor certification, interviews, measured savings or clinical validation. Report current stage and milestones, not a new overall percentage.
- Preserve literal-answer mutation failure and real browser transport failures. Actual file/component/browser/fresh-install evidence are distinct. No agent/source-review signature or production promotion is created.

## 18 October 2026: private browser demonstration

- Follow the user's final-hour request with a focused one-spreadsheet web interface,
  original dark/yellow design inspired by the event palette, and an evidence-backed
  presentation. Do not claim a complete clinical operations product.
- Reuse exact Python core sources through a Pyodide module worker instead of
  reimplementing timing logic in JavaScript. Keep runtime assets on the same origin
  after actual external/classic-worker failures. Pin hashes and include licenses.
- Preserve rule, schema, viewer and Streamlit behavior. The browser route does not
  include saved-report comparison or the three-file intake UI.
- Keep structured missing/conflicting information separate from timing conclusions.
  A source date is never estimated. Display invalid dates literally.
- All calculations use supplied bytes; actual downloads match native Python on the
  tested case. Changing one source date changes the computed days outside.
- The user explicitly chose owner-private hosted access. Deployment success is
  separate from owner authentication, which failed in the in-app browser. No
  access widening or authentication bypass is authorized.
- Research establishes relevance of the underlying issues, not TrialTrace's savings,
  customer demand or clinical validation. Retain independent review as pending.
