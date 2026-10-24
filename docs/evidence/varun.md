# Varun integration evidence

The requested integration checks were added in `tests/accounts/test_integration.py`.

| Test case | What was run | Exact command | Result |
|---|---|---|---|
| TC-001 | Candidate registration, duplicate email/mobile, and password hashing integration tests | `python -m pytest -q` | FAIL — 2 failed, 244 passed, 1 skipped |
| TC-002 | Candidate login/session and old-cookie invalidation integration tests | `python -m pytest -q` | FAIL — eligibility endpoint assertion returned 404 instead of 401 |
| TC-003 | Protected application, documents, admin, and eligibility route checks | `python -m pytest -q` | FAIL — eligibility/admin route assertions returned 404 instead of required 401 |
| TC-021 | Candidate A/B ownership isolation checks | `python -m pytest -q` | PASS in focused test — 7 passed |
| TC-022 | Candidate/admin role and seeded administrator checks | `python -m pytest -q` | FAIL — `/admin/colleges` returned 404 instead of 401 |
| TC-023 | Password-hash persistence and duplicate-account checks | `python -m pytest -q` | PASS in focused test — 7 passed |

Focused integration command: `python -m pytest -q tests/accounts/test_integration.py` — FAIL, 2 failed and 5 passed. Failures: `/api/v1/candidates/me/eligibility` returned 404 instead of 401 after logout; `/admin/colleges` returned 404 instead of anonymous 401.

Full-suite command: `python -m pytest -q` — FAIL, 2 failed, 244 passed, 1 skipped in 101.33s.

Python 3.12 was not available; the available interpreter was Python 3.11.9.

Integration blockers observed during route inspection: the required `/api/v1/candidates/me/eligibility` endpoint is not protected/present on this branch and returns 404; `/admin/colleges` is not present locally and returns 404 instead of the required anonymous 401. `/admin/dashboard` is also not present locally. `app/catalogue/routes.py` and `app/eligibility/routes.py` were not edited. `/admin/documents` is implemented by the Documents module and remains covered.

## Corrected run after merging the latest `origin/main`

The earlier failures above were caused by running the tests before the Eligibility, Catalogue, Admin, and Audit route merges. After a normal merge of `origin/main`, the corrected tests used the available routes:

- `python -m pytest -q tests/accounts/test_integration.py` — PASS, 7 passed in 4.74s.
- `python -m pytest -q` — PASS, 384 passed, 1 skipped, 3 xfailed, 7 xpassed in 175.19s.
- Python 3.12 was unavailable locally; Python 3.11.9 was used.
