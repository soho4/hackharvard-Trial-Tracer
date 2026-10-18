# Build progress — 18 October 2026

**Current stage: functioning local synthetic prototype, before independent pilot validation.** There is no defensible overall-product completion percentage yet. The previous 75→100 score measured only a bounded local workflow checklist, not production readiness or completed clinical validation. Its original rubric remains in [the historical workflow baseline](review/workflows/BASELINE_REVIEW.md) and [historical technical gate](gates/WORKFLOW_TECHNICAL.json).

| Milestone | Current state |
|---|---|
| Process actual supplied files through a deterministic check | Working for one draft Table 21 timing rule |
| Inspect original evidence, uncertainty and saved-run differences | Implemented; prior browser evidence retained and current regression suite passes |
| Prepare one spreadsheet with visible mapping and complete provenance | Implemented; actual file, browser downloads and fresh installed environment verified |
| Research export assumptions and existing alternatives | First primary-documentation pass completed; useful workflow remains a hypothesis |
| Independently confirm source interpretation and applicable records | Pending human review; G0 blocked |
| Fit a real configured export and verify its dictionary | Pending; current example is authored synthetic data, not a vendor export |
| Demonstrate user benefit and total time saved | Pending; no interviews, workflow study or measured savings |
| Another person/machine reproduces results | Pending; fresh installation was on this Mac |
| Production data handling, deployment and operations | Outside implemented local scope |

Current technical evidence: **447 application tests passed**, actual browser output matches installed CLI and complete source-preserving package, and fresh regular-wheel installation succeeds. Browser transport failures during malformed-file attempts are retained; a subsequent file reached the parser and was correctly rejected. See [acceptance](review/preparation/ACCEPTANCE.md).

The next useful milestone is a reviewer-verified synthetic export from an actual configured workflow, a field dictionary and independently worked answers. Source/rule review and a preparation-inclusive comparison against the existing process are separate gates. [Validation plan](PILOT_VALIDATION_PLAN.md) and [honest demo script](HACKATHON_DEMO.md) are ready to use; neither represents completed field research.
