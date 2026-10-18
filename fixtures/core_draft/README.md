# Draft engineering inputs, not source approval

These are three real authored CSV files with ten cases defined before the new importer/engine exists. The rule remains A10_DRAFT_2, pending source review. Every person and event is synthetic.

`DRAFT_SYNTHETIC` is an explicit v4 input mapping label; it is not a human approval. Only an opt-in DRAFT_ENGINEERING invocation may calculate under it. Normal reviewed mode must not silently accept these as reviewed. H09 deliberately remains UNRESOLVED.

`expected.json` belongs to the test harness, never the application's runtime. It states proposed engineering expectations, not outputs already measured from a working new engine. H10 is a synthetic leap-year example, not a claim about an event that occurred.

After implementing these cases, author additional files with new identifiers and changed dates, then run them through the actual CLI. Do not prove functionality only by reading this bundled scenario.
