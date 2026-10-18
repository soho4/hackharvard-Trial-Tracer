# What actually works, and what it proves

| Capability | Current behavior and evidence |
|---|---|
| Public study source | Real ClinicalTrials.gov API snapshot and original public protocol identity evidence; dated snapshot, not a live feed |
| CSV input | User-supplied bytes, strict parsing, exact hashes, preserved rows; no fixture fallback |
| Identity joins | Study/participant/site validation, duplicates and unresolved references exposed |
| Timing calculation | One supported Table 21 OL-D8 candidate rule; inclusive calendar-day math, tested on varied dates and new identifiers |
| Uncertainty | DATA_QUERY and NOT_EVALUABLE retain evidence and omit confident timing calculations |
| Upload app | Actual local Streamlit server, three uploads, explicit draft mode, clear-before-replacement, recalculation |
| Evidence inspection | Original rows, ordinals, hashes, selected finding, filters/search; all input accounting remains visible |
| JSON export | Same Python functions as CLI; actual browser downloads byte-identical to CLI and unaffected by display filters |
| Saved-report viewer | Upstream reader integrated against unchanged contract; focused date/wrapping fixes; reads reports but does not rerun the engine |
| Installation | Fresh pinned Python 3.13 environment and regular wheel verified on this Mac |
| Human-reviewed rule | **Pending.** No human approval or clinical validation record exists |
| Real participant evaluation | **Unsupported.** The public registry provides no matching participant visit records; all operational inputs used here are synthetic |
| Other trials/rules, arbitrary PDFs | **Not implemented.** Unsupported event/anchor/scope records do not become confident findings |
| Missed-activity/eligibility inference | **Not implemented.** Missing records do not prove that an activity was missed |
| Clinical/regulatory decisions | **Not provided.** Potential deviations require review; PASS covers only the stated draft timing check |
| Public deployment, production auth/database | **Not performed/implemented.** Local engineering app only |

The next meaningful validation step is independent human review of the exact
protocol interpretation and independently worked examples. A future real-data
pilot also needs an explicitly authorized dataset, real mapping review, and a
separately agreed data-handling scope. More synthetic tests cannot substitute for that.
