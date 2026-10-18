# Independent G1 technical review

Read-only review of importer, relationships, import CLI, v4 section 7, and the acceptance matrix. No implementation, test expectations, candidate rule, or human source review was changed.

## Findings

1. **P1 before export promotion: duplicate evidence permits quadratic expansion before output limits can be checked.** `relationships.py` lines 78-94 creates a fresh evidence wrapper for every matching duplicate in every visit, and copies all candidate issues into every visit. The probes use valid structural inputs and stay below all three input limits. Ten duplicates per table (largest input 91,231 bytes) produce 300 evidence entries and 2,204,732 serialized inspection bytes. Fifty duplicates (largest input 455,751 bytes) produce 7,500 evidence entries, 5,150 problem entries, and 50,692,652 serialized inspection bytes. These sizes were counted incrementally without allocating the whole JSON. At fifty records, inspection alone used about 2.6 MB peak additional traced memory; no claim is made that an OOM occurred. The current engine passes this evidence onward. Ensure CORE_EXPORT counts serialized bytes incrementally and stops with an explicit size error before a giant full `json.dumps`/canonical buffer is created. Cache immutable per-record evidence and per-row issue wrappers to reduce intermediate duplication. Add a below-input-limits duplicate-heavy acceptance case that proves explicit output rejection without evidence truncation. Exporter was not yet present during this review, so this is a demonstrated amplification risk to close during integration, not a claimed observed exporter failure.

2. **P2: sufficiently oversized cells receive a malformed-CSV diagnostic instead of the specified size-limit diagnostic.** `importer.py` lines 75-79 relies on the process-global `csv` field-size default (131,072), so a well-formed 140,000-character mapping note in a 140,214-byte assignment file raises `CSV_PARSE: Malformed CSV record` before the 10,000-character policy check. The +1 boundary test passes, but larger legal-CSV cells are mislabeled. Enforce the cell bound during scanning or otherwise normalize the parser's field-limit failure into `CELL_SIZE_LIMIT` without accepting oversized data. Add this large-cell diagnostic case.

## Verification and scope

- Existing focused suite: `55 passed in 0.25s` for `tests/test_importer.py tests/test_relationships.py` with cache writes disabled and temporary files outside the repository.
- Probe source and results: `probe.py` and `probe_results.json` beside this report. Results bind exact reviewed implementation hashes.
- Parser review found no silent row loss in the exercised LF/CRLF, BOM, quoted multiline, reordered-header, or duplicate-key paths.
- Wrong-person/site joins currently retain the candidate in `joined`, but also add `DATA_QUERY`; the inspected engine checks all problems before arithmetic. No cross-identity calculation bug was demonstrated.
- Source interpretation and G0 acceptance were not part of this review.
