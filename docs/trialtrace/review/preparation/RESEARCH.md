# Research and product hypothesis — 18 October 2026

This is desk research from primary documentation, not interviews, a market study, a vendor integration certification or evidence of time saved. Public documentation was opened on 18 October 2026. No trial account, proprietary export or participant record was accessed. The existing public protocol and dated registry snapshot remain the only actual study sources used.

| Primary source checked | Observation | Consequence for TrialTrace |
|---|---|---|
| [OpenClinica Extract Data](https://servicedesk.openclinica.com/support/solutions/articles/158000422773-extract-data) | Extracts select events/forms/items and attributes. Permissions and archived-form defaults can omit data. Tabular formats include TSV, HTML and Excel, with metadata and data sections. Repeat occurrences appear in identifiers. | The three internal CSVs are our contract, not a universal trial export. The new flat CSV mapper is not a direct OpenClinica importer. A missing record cannot establish a missed activity. |
| [OpenClinica Calendar introduction](https://servicedesk.openclinica.com/support/solutions/articles/158000442542-calendar-introduction) and [Rules](https://servicedesk.openclinica.com/support/solutions/articles/158000436446-rules) | Existing products already configure event scheduling and rules. | Generic date checking alone is not a substantiated unmet need. Compare against the team's actual system, not an invented manual-only baseline. |
| [CDISC SDTMIG v3.3](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-3/html), Subject Visits and Exposure | Visit dates can be derived using data from other domains; exposure has its own representation. This particular version is a documentation example, not a claim about the latest standard. | A generic visit date cannot silently become an actual vaccination date. SDTM is not implemented or certified here. |
| [REDCap software overview](https://projectredcap.org/software/) | Configurable capture, export and data-management facilities exist. | Study configuration and a data dictionary are needed before asserting that a named column has a particular meaning. This is not a REDCap connector. |
| [Medidata EDC overview](https://www.medidata.com/en/data-experience/edc-systems/) | Existing EDC offerings include data management and review capabilities. | Do not pitch TrialTrace as introducing data review to an industry without it. |

## What we can reasonably try

**Hypothesis, not a validated customer need:** a reviewer who already works with exported data may benefit from a small, portable package showing original bytes → chosen fields → declared scope → generated input tables → timing calculation → unresolved evidence. That package may make a specific review easier to reproduce or explain outside the source system.

The likely bottleneck is finding the correct event, anchor and applicable rule, then explaining a flag. The arithmetic itself is small. If preparing exports takes longer than the review work saved, or the existing EDC already provides the needed evidence, this tool may add no value. We must measure the complete workflow.

## Engineering response in this increment

The first tab now lets a user explicitly map eight fields in one wide CSV, choose the exact value meaning an actual call was completed, inspect a preview and declare synthetic draft Table 21 scope. It retains every source row and unused column. The complete downloadable package preserves original source bytes, mapping, declared constants, generated tables and existing evidence JSON. Column meanings and applicability are declarations, not inferred facts or approval.

This prototype requires both actual dates and necessary identifiers on each row. Longitudinal records on separate rows, partial dates, repeating instruments, additional protocol versions and incomplete exports need separately specified adapters or must remain unsupported. Repeated vaccination IDs remain duplicate-key queries; they are not silently collapsed. We did not obtain an actual vendor export, so the new authored CSV proves mechanics only.

## What would change the decision

Proceed toward an adapter only after a reviewer supplies a synthetic export from their actual configured workflow and its dictionary, demonstrates a concrete review burden, and verifies the relevant field meanings. Continue toward a pilot only after independent source/rule review and independently adjudicated examples. Stop or redirect if no meaningful burden exists or preparation outweighs the benefit. See [the validation plan](../../PILOT_VALIDATION_PLAN.md). No outreach or interview has been performed.
