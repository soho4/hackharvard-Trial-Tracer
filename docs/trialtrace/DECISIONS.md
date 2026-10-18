# Decisions

- User explicitly identified existing GitHub repository; clone is work/TrialTrace. Main was clean with only README and ignore file. No repository AGENTS instructions existed. New feature branch codex/trialtrace-core-v4. Separate origin/abinet/evidence-viewer branch is preserved and not merged.
- Python src package, pytest, jsonschema; no runtime model, frontend, database or service.
- Retain exact candidate/schema/fixtures. Source review remains pending. Reviewed execution fails closed; explicit draft CLI mode is required.
- Requirement and expected outcomes are frozen in CORE_ACCEPTANCE.md before implementation; separate test author owns application tests.
- Canonical JSON: UTF-8, sorted keys, compact separators, ensure_ascii=False, allow_nan=False, final newline. No generated timestamp in result content.
