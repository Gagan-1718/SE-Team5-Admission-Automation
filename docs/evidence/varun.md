# Varun integration evidence

The requested integration checks were added in `tests/accounts/test_integration.py`.

| Test case | What was run | Exact command | Result |
|---|---|---|---|
| TC-001 | Candidate registration, duplicate email/mobile, and password hashing integration tests | `python -m pytest -q` | PASS — 246 passed, 1 skipped |
| TC-002 | Candidate login/session and old-cookie invalidation integration tests | `python -m pytest -q` | PASS — 246 passed, 1 skipped |
| TC-003 | Protected application, documents, admin, and eligibility route checks | `python -m pytest -q` | PASS — 246 passed, 1 skipped |
| TC-021 | Candidate A/B ownership isolation checks | `python -m pytest -q` | PASS — 246 passed, 1 skipped |
| TC-022 | Candidate/admin role and seeded administrator checks | `python -m pytest -q` | PASS — 246 passed, 1 skipped |
| TC-023 | Password-hash persistence and duplicate-account checks | `python -m pytest -q` | PASS — 246 passed, 1 skipped |

Focused integration command: `python -m pytest -q tests/accounts/test_integration.py` — PASS, 7 passed in 4.77s.

Full-suite command: `python -m pytest -q` — PASS, 246 passed, 1 skipped in 106.34s.

Python 3.12 was not available; the available interpreter was Python 3.11.9.

Owner gaps observed during route inspection: `app/catalogue/routes.py` and `app/eligibility/routes.py` do not exist. `/admin/colleges`, `/admin/dashboard`, and `/admin/audit-logs` are not implemented; `/admin/documents` is implemented by the Documents module. These gaps were not changed.
