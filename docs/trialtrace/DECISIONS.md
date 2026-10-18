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
