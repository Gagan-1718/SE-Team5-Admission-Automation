# Sprint 2 Defect Log

Defects are recorded only when reproduced by a test or a repeatable inspection.
Gagan owns final triage and disposition.

| ID | Summary | Module | Severity | Owner | Status / disposition |
|---|---|---|---|---|---|
| VARUN-001 | Dashboard document tile reported only `0 of 3` or `3 of 3`, so one or two approved required documents were displayed inaccurately. | Candidate Dashboard / Documents contract | Medium | Dikshith | Fixed; Dashboard now consumes the Documents-owned approved-document summary service. |

## VARUN-001 — approved-document count

- Original observed behavior: `app/accounts/routes.py` used the binary expression `"3 of 3" if all_documents_approved(candidate_id) else "0 of 3"`.
- Reproduction: render `/dashboard` for a candidate with exactly one or two approved required document types; the tile cannot represent the actual count and returns `0 of 3`.
- Expected behavior: 0, 1, 2 and 3 approved required documents display as `0 of 3`, `1 of 3`, `2 of 3` and `3 of 3` respectively. Pending, rejected, resubmitted and missing documents must not count as approved.
- Evidence before fix: inspection of `app/accounts/routes.py` and `app/documents/services.py`; the Documents module exposed `all_documents_approved(candidate_id)` but no approved-count summary service.
- Resolution: added the read-only `get_document_summary(candidate_id)` service using `REQUIRED_DOCUMENT_TYPES`, distinct approved required types, candidate scoping and the existing `Approved` status. The Dashboard now renders `approved_count of required_count` and does not query Documents tables directly.
- Verification: `py -m pytest -q tests/documents` — 176 passed; `py -m pytest -q tests/accounts/test_dashboard.py` — 20 passed; `py -m pytest -q tests/accounts tests/documents` — 241 passed; `py -m pytest -q` — 802 passed, 1 skipped, 6 xpassed.
- Disposition: fixed and regression-tested. No upload, review, rejection or resubmission workflow was changed.
