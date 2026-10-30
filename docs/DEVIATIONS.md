# Deviations from the submitted SRS, SAD and Test Plan

Status date: **21 October 2026** (Sprint One, day 3). This file records every place where the product differs from the documents we submitted, why, and what we will say in the final demo. The SRS stays authoritative: **no functional or security requirement was dropped or changed**; the differences below are design and implementation choices. Items in section 3 are not finished yet; `python -m pytest -q tests/integration/test_demo_flow.py -rx` lists them as expected failures with the reason.

## 1. Technology (documented earlier)

| Submitted | Built | Why |
|---|---|---|
| Java, Spring Boot, MySQL | Python 3.12, Flask, Flask-SQLAlchemy, SQLite | Team decision on 19 Oct 2026 for a small academic demonstration. Recorded in `DOCUMENT_CHANGE_RECORD.md`, `SAD_Python.md` and `TEST_PLAN_PYTHON_ADDENDUM.md`. |
| JUnit style tests | pytest and the Flask test client | Same addendum. |

## 2. Design differences in modules already merged into `main`

| # | Area | Submitted (SAD) | Built | Reason | Impact |
|---|---|---|---|---|---|
| D-01 | Password hashing | BCrypt | Werkzeug `scrypt` with a unique salt per password | Built into the framework already in use; still a salted, one-way, adaptive hash. SEC-F-003 names no algorithm. | SEC-F-003 is met. |
| D-02 | Login sessions | Flask-Login and Flask-Session | A small custom `user_sessions` table. The browser cookie `team5_session` holds a random token; only its SHA-256 hash is stored. Expires after 8 hours. Cookie is `HttpOnly`, `SameSite=Lax`, and `Secure` when served over HTTPS. Logout deletes the server-side row, so an old cookie stops working (tested). | Fewer dependencies and full control of logout invalidation. | SEC-F-001 and logout invalidation are met. |
| D-03 | CSRF protection | Flask-WTF CSRF on state-changing requests | **Not implemented on `main`.** The login cookie uses `SameSite=Lax`, which blocks the common cross-site form post, but there is no CSRF token. | Not completed in Sprint One. | A real gap against the test plan addendum ("keep CSRF protection"). Planned for Sprint Two. Documents upload form (pending merge) already has a form token. |
| D-04 | Account endpoints | `POST /api/v1/auth/register`, `/auth/login`, `/auth/logout`; `PUT /candidates/me/exam-details` | `POST /accounts/register`, `/accounts/login`, `/accounts/logout`; `PUT /accounts/exam-details`; also `GET /accounts/me`, `/accounts/profile` | One blueprint per module under its own prefix. | Request and response shapes follow the SAD; only the paths differ. Update the SAD table in the final documentation. |
| D-05 | Registration fields | name, email, mobile, **date of birth**, password (ADM-F-001) | name, email, mobile, password. **Date of birth is not collected.** | The shared User contract agreed on 19 Oct has no date of birth field. | A small gap against ADM-F-001. Can be added to `users` without changing other modules. |
| D-06 | Status names | Document "Pending Verification"; Eligibility "Pending Verification" | Document `Pending`; Eligibility `Pending` | Shared contract agreed by the team on 19 Oct (Pending, Approved, Rejected; Pending, Eligible, Not Eligible). | Meaning is identical. Display text can say "Pending Verification". |
| D-07 | Application form fields | Not defined in the SRS | `guardian_name`, `guardian_mobile`, `school_name`, `board`, `percentage`; all mandatory to submit | The SRS says "mandatory fields" without listing them. | Provisional list, easy to change in one place (`app/application/models.py`). |
| D-08 | Reference number | "Unique reference number" | `ADM-YYYY-NNNNNN` (year plus the never-reused application id) | Simple, unique, readable. A database rule makes a reference exist exactly when the status is Submitted. | ADM-F-005 is met. |
| D-09 | Rank and category | Taken from the seeded exam record (assumption A-09) | As designed: `PUT /accounts/exam-details` accepts only a combination that exists in the seeded `exam_records` table | (no deviation, recorded for completeness) | Candidates cannot type their own rank or category. |
| D-10 | HTTPS | HTTPS/TLS with a locally generated certificate acceptable (A-16) | Cheroot server with a self-signed certificate for `localhost`, TLS 1.2 or newer, HTTP redirects to HTTPS, HSTS header. Run with `python scripts/serve_https.py`. | A-16. | Lab setup only, not an internet deployment. Browsers show "Not secure" because the certificate is self-signed. |
| D-11 | Administrator account | Created by a seed script (A-05) | As designed, with the password read from the `ADMIN_SEED_PASSWORD` environment variable (or generated and printed once); never stored in Git | (no deviation) | Meets the "no secrets in Git" rule. |
| D-12 | Candidate pages | HTML5, CSS/Bootstrap, minimal JavaScript | Jinja pages with plain CSS (no Bootstrap); the account pages call the JSON API with JavaScript | Fewer external dependencies. | Same screens as SAD 4.5. |
| D-13 | Document endpoints | `POST /documents`, `GET /documents`, `PUT /documents/{id}`, `GET /admin/documents?status=Pending`, `PUT /admin/documents/{id}/review` | `GET/POST /documents/upload`, `GET /documents`, `POST /documents/<id>/resubmit`, `GET /admin/documents` and `/admin/documents.json`, `POST /admin/documents/<id>/review`, `GET /admin/documents/<id>/file`. Upload, resubmission and review forms carry a form token. Uploads are stored in `instance/uploads/` under random names; PDF and image contents are checked, not just the extension. | HTML forms use POST; the file view and the content checks were added for safety. | Same behaviour as SAD 4.3.3 (415 and 413 become a form error with 400). This also partly answers D-03: the document forms have a CSRF token. |
| D-14 | Catalogue endpoints | `GET /colleges?search=`, `POST/PUT /admin/colleges`, `/admin/colleges/{id}/branches`, `/admin/seat-matrix` (JSON) | `GET /colleges` with filters `q` and `college_id`; admin pages `/admin/colleges`, `/admin/colleges/new`, `/admin/colleges/<id>/edit`, `/admin/colleges/<id>/branches/new`, `/admin/branches/<id>/edit`, `/admin/branches/<id>/seats` (HTML forms). Duplicates return 409 and invalid capacity 422. Seat categories: General, OBC, SC, ST, EWS. | Server-rendered admin screens fit the Flask design. | Same rules as ADM-F-010 and ADM-F-011. The admin guard denies by default and still has to be connected to the administrator login. |
| D-15 | Eligibility | Rules as editable data, status with reason (ADM-F-009) | Pure decision function with `eligibility_rules` rows (category, cut-off rank, active). Order: Pending while documents are not all approved, Not Eligible if the rank is above the cut-off or no rule exists, otherwise Eligible. Cut-offs are fictional sample data. | SAD A-08 and A-06. | Rules are data, not code. Not yet connected to the real exam details and documents (section 3). |

## 3. Not finished yet (status 21 October 2026)

| # | Area | What is missing | Owner |
|---|---|---|---|
| P-01 | Candidate exam details in the browser | The API `PUT /accounts/exam-details` works, but the profile page has no exam-details form yet. | Varun |
| P-02 | `all_documents_approved(candidate_id)` and the required document types | Not in `app/documents/services.py` yet; the upload accepts any document type text instead of only Marksheet, ID Proof and Category Certificate (proposed). Documents are not yet linked to users and applications by foreign keys, and review actions do not write audit entries. | Dikshith |
| P-03 | Eligibility connection | Eligibility still uses sample inputs (rank 1000, General) and its pages are not login-protected. It must read the real exam details and the document approval status. | Tasya |
| P-04 | Catalogue admin access | The admin pages deny everyone because the guard is not connected to the administrator login yet. | Tasya |
| P-05 | Audit log and admin dashboard (SEC-F-005, ADM-F-020) | Not built yet. The audit log will be append-only through database triggers, as in SAD A-17. | Tasya |
| P-06 | CSRF protection | Not on the accounts, application, catalogue and eligibility forms (only the document forms have a token). Planned for Sprint Two. | Team |
| P-07 | Test evidence | Results are recorded in `docs/evidence/` by each owner. A test case is only marked passed after it was run. | Everyone |

## 4. Out of Sprint One scope (by design, Sprint Two)

Choice filling, ordering and locking; seat allotment and Not Allocated; result publication and the accept/reject decision; performance and consistency testing; configuration screens (see `SPRINT_ONE_START_HERE.md`).

## 5. How we work (process notes)

- One feature branch per task, pull requests into `main`, a CI check (`.github/workflows/ci.yml`) runs the tests on every push and pull request.
- Fictional data only; no database file, upload, certificate, key or password is committed.
- Pull requests are raised by each module owner and reviewed and merged by the repo owner on GitHub. Some early merges (foundation, accounts, application) were done from the command line to unblock the team; their pull requests were closed as "already merged into main".

## 6. Sprint Two contract choices (30 October 2026)

These are recorded for completeness when the choice, allotment and result tables were agreed (`SPRINT_TWO_START_HERE.md` section 4). No requirement changed.

| # | Area | Submitted (SAD) | Built | Reason | Impact |
|---|---|---|---|---|---|
| D-16 | Where "published" is stored | SAD 4.1: the allotment run moves from Completed to Published | A separate `result_publications` table owned by the Result module, with a unique `run_id` | One owner per module; "publish once" becomes a database rule instead of a status the Allotment module would also have to change | ADM-F-017 behaves the same: results are hidden until the administrator publishes |
| D-17 | Paths and pages | `/api/v1/choices`, `/api/v1/admin/allotment/run`, `/api/v1/allotment/result` and so on | Exactly those API paths, plus HTML pages `/choices`, `/result`, `/admin/allotment` | The SAD defines the API only; the pages are the Flask screens in SAD 4.5 | No deviation, recorded for completeness |
| D-18 | Rules enforced by the database | A-07, A-13, ADM-NFR-003 describe the rules | `allotment_runs.cycle` is always 1 and unique (one cycle); run counts must add up; an `Allocated` result must have a branch, seat and choice number and a `Not Allocated` one must have none; `choices` refuses a branch twice per candidate; `seat_decisions` allows one row per result | Even a bug in application code cannot break these rules | Stricter than the SAD text, same intent |
