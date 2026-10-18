# TrialTrace technical source check

Technical acquisition succeeded on 2026-10-18. This record is new execution evidence; historical package claims were not treated as current evidence. The candidate and all human-review fields remain unchanged. No repository, application, or frontend was modified.

- Exact source URL: https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf
- Preserved bytes: `.sources/Prot_000.pdf` in the original local `work/source_check/` directory only; no PDF or rendered page is included in this repository.
- SHA-256: `da946b1ae23d40c41b332f1d0cb3311f0634e57009b4a37b9c6d6c60ee8bf186`.
- Size: 2,728,675 bytes. PDF page count: 193.
- Acquisition: native curl, HTTP 200, application/pdf, no redirects, TLS verification result 0. UTC start/end: `2026-10-18T07:19:26.152214+00:00` / `2026-10-18T07:19:26.506238+00:00`.
- Result: unmodified supplied `verify_source.py --pdf` exited 0; all eight identity/context checks passed. Its generic local-copy acquisition label is preserved in `verifier_local_manifest.json`; actual origin evidence is separately captured in curl records.

## What actually ran

The supplied verifier was read before execution. First run used bundled Python and returned HTTP 200, then exited 2 because PyMuPDF was absent; that script did not save the downloaded bytes on failure. An isolated `.venv` was created here and the supplied pinned dependency `PyMuPDF==1.26.7` installed. The venv's network verifier attempt exited 2 on a local issuer certificate-trust error. No TLS check was bypassed. Native curl then acquired the PDF successfully. The verifier's local-file mode and bundled `pdfinfo` both exited 0. Bundled `pdftoppm` rendered pages 1 and 150-152; both rendering commands exited 0, and the resulting PNGs were inspected visually.

Every acquisition, dependency, verification and rendering command has exact arguments, working directory, UTC start/end, exit code, raw stdout and stderr in `logs/`. `source_check_manifest.json` binds these records, exact PDF bytes, inspected verifier, unchanged candidate, and rendered pages with SHA-256 hashes. The initial failures remain preserved. A web open of the same URL independently returned the expected 193-page identity; it is not represented as local-byte evidence.

## Model visual observations, not approval

The cover shows NCT04470427, mRNA-1273-P301, Amendment 10, April 7, 2022. Page 150's Table 21 limits its schedule to the specified Part A placebo cohort. Its OL-D8 column shows SC, seven days after OL-D1, and a +3-day allowance. Page 151 expands SC as a safety phone call. Page 152 contains separate-visit context for Day 0 and OL-D1 and call-assessment context. These are technical observations only. [Public source](https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf)

The source's displayed note numbering needs reviewer attention: rendered page 152 labels run 4-11, while the table's superscripts run 1-8. Preserve this discrepancy when locating notes; do not silently rewrite the numbering.

## Remaining blockers

G0 is still blocked by actual independent human source-interpretation review bound to the PDF and candidate hashes. The candidate's zero-early allowance and inclusive endpoints remain unapproved. No reviewer name, signature, boolean approval, or completed review artifact was created. File fingerprints and token checks do not prove clinical validity, interpretation, or review authorship.

The PDF and rendered source pages remain local in `.sources/`; they are not a public deliverable and must not be committed or published. No source substitution, candidate change, or clinical implementation occurred.
