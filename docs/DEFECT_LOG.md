# Sprint 2 Defect Log

Defects are recorded only when reproduced by a test or a repeatable inspection.
Gagan owns final triage and disposition.

| ID | Summary | Module | Severity | Owner | Status / disposition |
|---|---|---|---|---|---|
| VARUN-001 | Dashboard document tile reports only `0 of 3` or `3 of 3`, so one or two approved required documents are displayed inaccurately. | Candidate Dashboard / Documents contract | Medium | Dikshith | Open and blocked pending a Documents-owned approved-count service; do not duplicate Documents logic in Accounts. |

## VARUN-001 — approved-document count

- Original observed behavior: `app/accounts/routes.py` used the binary expression `"3 of 3" if all_documents_approved(candidate_id) else "0 of 3"`.
- Reproduction: render `/dashboard` for a candidate with exactly one or two approved required document types; the tile cannot represent the actual count and returns `0 of 3`.
- Expected behavior: 0, 1, 2 and 3 approved required documents display as `0 of 3`, `1 of 3`, `2 of 3` and `3 of 3` respectively. Pending, rejected, resubmitted and missing documents must not count as approved.
- Evidence: inspection of `app/accounts/routes.py` and `app/documents/services.py`; the Documents module exposes `all_documents_approved(candidate_id)` but no approved-count summary service.
- Regression test needed: Documents-owned summary-service tests for all four counts plus candidate ownership isolation, followed by a Dashboard integration test.
- Disposition: not fixed in this branch because the authoritative service is owned by Dikshith and does not exist. No Documents tables are queried from Accounts and no duplicate Documents logic was added.
