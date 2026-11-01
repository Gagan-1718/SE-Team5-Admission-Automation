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

## Current synchronized feature-branch verification — 1 November 2026

These results were run on `feature/candidate-dashboard` at `7b1bc240da147e12200569fb58fa9b70ff862200`, which includes `origin/main` at `5a4f7b94a592f7ddb9fd8015c2bf6aca72b6f64d`. They are not evidence from `main`; PR #76 remains under review. Python 3.12 was unavailable (`py -3.12 --version` found no suitable runtime), so the available Python version was Python 3.11.9.

| Test case | Requirement verified | Exact command | Actual result |
|---|---|---|---|
| TC-001 | Registration validation, DOB, duplicate email/mobile and password hashing | `py -m pytest -q tests/accounts/test_registration.py tests/accounts/test_profile_integrity.py` | PASS — 9 passed |
| TC-002 | Login/logout and session behavior | `py -m pytest -q tests/accounts/test_login_logout.py` | PASS — 4 passed |
| TC-003 | Protected routes, role checks and cross-module Accounts integration | `py -m pytest -q tests/accounts/test_protected_routes.py tests/accounts/test_integration.py` | PASS — 11 passed |
| TC-012 | Choice add/remove/preview and duplicate/ownership rules | `py -m pytest -q tests/choices/test_add.py tests/choices/test_remove.py tests/choices/test_listing.py tests/choices/test_routes.py` | PASS — 17 passed |
| TC-013 | Choice reorder and persistence contract | `py -m pytest -q tests/choices/test_reorder.py` | PASS — 7 passed |
| TC-014 | Choice locking and post-lock refusals | `py -m pytest -q tests/choices/test_lock.py` | PASS — 4 passed |
| TC-021 | Candidate ownership isolation | `py -m pytest -q tests/accounts/test_integration.py -k 'candidate_a or ownership'` | PASS — 2 passed, 5 deselected |
| TC-022 | Candidate/admin authorization behavior | `py -m pytest -q tests/accounts/test_integration.py -k 'authorization or admin'` | PASS — 1 passed, 6 deselected |
| TC-023 | Salted password hashing and credential-store checks | `py -m pytest -q tests/accounts/test_password_hashing.py tests/accounts/test_registration.py` | PASS — 8 passed |

Regression run on this synchronized feature branch: `py -m pytest -q` — PASS, 738 passed, 1 skipped, 6 xpassed. `git diff --check` passed.

### Current integration dependencies

- The Documents module still exposes `all_documents_approved(candidate_id)` but no read-only `get_document_summary(candidate_id)` approved-count service. The Dashboard therefore cannot truthfully display `1 of 3` or `2 of 3` without a Documents-owned contract; this remains pending Dikshith.
- `app/documents/journey.py` remains a locked-step stub pending Dikshith's implementation.
- `app/results/journey.py` remains a locked-step stub pending Dikshith's Results/Decision integration.
- `app/eligibility/journey.py` remains a locked-step stub pending Tasya's implementation.
- `app/application/journey.py` and `app/choices/journey.py` provide real journey states on this branch.

Manual 400px responsive, keyboard-only, and contrast verification were not performed in this run.

## Final feature-branch verification — 1 November 2026

The final verification was run on `feature/candidate-dashboard` at commit
`263fec15d56bbf3e42fabffb642f74880a2e2041` after the dashboard scenario and
next-action tests were corrected. `origin/main` remained
`5a4f7b94a592f7ddb9fd8015c2bf6aca72b6f64d`; these results are feature-branch
evidence, not evidence from merged `main`.

Python: 3.11.9. Python 3.12 was unavailable in the local launcher.

| Scope | Exact command | Actual result |
|---|---|---|
| Dashboard | `py -m pytest -q tests/accounts/test_dashboard.py` | PASS — 16 passed |
| Accounts and Choices | `py -m pytest -q tests/accounts tests/choices` | PASS — 114 passed |
| Full regression | `py -m pytest -q` | PASS — 741 passed, 1 skipped, 6 xpassed |
| Diff validation | `git diff --check` | PASS |

The dashboard now explicitly covers the documented `NOT_ALLOCATED` problem state,
first-problem selection, first-current selection, and the no-actionable-step case.
The real Documents, Eligibility, and Results providers remain external dependencies;
their current journey implementations are still stubs, so provider integration and
approved-document counts cannot be claimed complete here. Manual 400px, keyboard-only,
and contrast verification were not performed.

## Post-main Sprint 2 verification — 1 November 2026

The feature branch was synchronized to `origin/main` at
`4983bfcdeece5ddfc6ab8c7ed831f3b799e826dc` before this run. The tests below ran on
`feature/candidate-dashboard` at `82a46ac` with Python 3.11.9. Python 3.12 was
unavailable: `py -3.12 --version` returned `No suitable Python runtime found`.

| Test case | Exact command | Actual result |
|---|---|---|
| TC-001 | `py -m pytest -q tests/accounts/test_registration.py tests/accounts/test_profile_integrity.py` | PASS — 9 passed |
| TC-002 | `py -m pytest -q tests/accounts/test_login_logout.py` | PASS — 4 passed |
| TC-003 | `py -m pytest -q tests/accounts/test_protected_routes.py tests/accounts/test_integration.py` | PASS — 11 passed |
| TC-012 | `py -m pytest -q tests/choices/test_add.py tests/choices/test_remove.py tests/choices/test_listing.py tests/choices/test_routes.py` | PASS — 17 passed |
| TC-013 | `py -m pytest -q tests/choices/test_reorder.py` | PASS — 7 passed |
| TC-014 | `py -m pytest -q tests/choices/test_lock.py` | PASS — 4 passed |
| TC-021 | `py -m pytest -q tests/accounts/test_integration.py -k 'candidate_a or ownership'` | PASS — 2 passed, 5 deselected |
| TC-022 | `py -m pytest -q tests/accounts/test_integration.py -k 'authorization or admin'` | PASS — 1 passed, 6 deselected |
| TC-023 | `py -m pytest -q tests/accounts/test_password_hashing.py tests/accounts/test_registration.py` | PASS — 8 passed |

Additional provider and cross-module run:

`py -m pytest -q tests/accounts tests/choices tests/documents tests/eligibility tests/results tests/integration tests/security`
— PASS, 447 passed, 6 xpassed.

Final full regression:

`py -m pytest -q` — PASS, 792 passed, 1 skipped, 6 xpassed.

`git diff --check` — PASS.

Eligibility and Results journey providers are now real and are exercised by their
provider tests and the Dashboard's shared `all_steps(candidate_id)` path. The
Documents journey is still a locked-step stub, and no approved-document count
service exists; the binary Dashboard count defect is recorded as VARUN-001 in
`docs/DEFECT_LOG.md` and remains blocked on Dikshith's public service contract.

Browser automation was attempted but unavailable: the Computer Use browser host
returned `The browser access host is unavailable`. Therefore 400px responsive,
keyboard-only, and contrast checks remain pending manual verification.
