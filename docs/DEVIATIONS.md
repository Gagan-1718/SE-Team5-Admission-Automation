# Deviations from the submitted SRS, SAD and Test Plan

Status date: **1 November 2026** (Sprint Two, day 3; first written 21 October 2026). This file records every place where the product differs from the documents we submitted, why, and what we will say in the final demo. The SRS stays authoritative: **no functional or security requirement was dropped or changed**; the differences below are design and implementation choices. The Sprint One gaps in section 3 are closed; what is still open is in section 7.

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
| D-03 | CSRF protection | Flask-WTF CSRF on state-changing requests | **Done in Sprint Two (#73).** A small check in `app/security.py` instead of Flask-WTF: a random token tied to the browser session, required on every POST, PUT, PATCH and DELETE, sent as a hidden `csrf_token` form field or an `X-CSRF-Token` header (the base template puts it in a meta tag for JavaScript). A missing or wrong token gives 400 `csrf_failed`. On top of the `SameSite=Lax` cookie. | One rule for every module, no new dependency. | The test plan addendum's "keep CSRF protection" is met. Tested in `tests/security/test_csrf.py` and `test_csrf_fetch.py`; a scripted POST without a token was refused with 400 on 1 Nov (Gagan's evidence). |
| D-04 | Account endpoints | `POST /api/v1/auth/register`, `/auth/login`, `/auth/logout`; `PUT /candidates/me/exam-details` | `POST /accounts/register`, `/accounts/login`, `/accounts/logout`; `PUT /accounts/exam-details`; also `GET /accounts/me`, `/accounts/profile` | One blueprint per module under its own prefix. | Request and response shapes follow the SAD; only the paths differ. Update the SAD table in the final documentation. |
| D-05 | Registration fields | name, email, mobile, **date of birth**, password (ADM-F-001) | **Done in Sprint Two (#72).** Registration requires name, email, mobile, `date_of_birth` (ISO date, must be in the past) and password. The JSON key is `date_of_birth`, not `dateOfBirth`. The column `users.date_of_birth` stays nullable so the seeded administrator and accounts made before the change still load. | Added without changing other modules. | ADM-F-001 is met for every new registration. |
| D-06 | Status names | Document "Pending Verification"; Eligibility "Pending Verification" | Document `Pending`; Eligibility `Pending` | Shared contract agreed by the team on 19 Oct (Pending, Approved, Rejected; Pending, Eligible, Not Eligible). | Meaning is identical. Display text can say "Pending Verification". |
| D-07 | Application form fields | Not defined in the SRS | `guardian_name`, `guardian_mobile`, `school_name`, `board`, `percentage`; all mandatory to submit | The SRS says "mandatory fields" without listing them. | Provisional list, easy to change in one place (`app/application/models.py`). |
| D-08 | Reference number | "Unique reference number" | `ADM-YYYY-NNNNNN` (year plus the never-reused application id) | Simple, unique, readable. A database rule makes a reference exist exactly when the status is Submitted. | ADM-F-005 is met. |
| D-09 | Rank and category | Taken from the seeded exam record (assumption A-09) | As designed: `PUT /accounts/exam-details` accepts only a combination that exists in the seeded `exam_records` table | (no deviation, recorded for completeness) | Candidates cannot type their own rank or category. |
| D-10 | HTTPS | HTTPS/TLS with a locally generated certificate acceptable (A-16) | Cheroot server with a self-signed certificate for `localhost`, TLS 1.2 or newer, HTTP redirects to HTTPS, HSTS header. Run with `python scripts/serve_https.py`. | A-16. | Lab setup only, not an internet deployment. Browsers show "Not secure" because the certificate is self-signed. |
| D-11 | Administrator account | Created by a seed script (A-05) | As designed, with the password read from the `ADMIN_SEED_PASSWORD` environment variable (or generated and printed once); never stored in Git | (no deviation) | Meets the "no secrets in Git" rule. |
| D-12 | Candidate pages | HTML5, CSS/Bootstrap, minimal JavaScript | Jinja pages with plain CSS (no Bootstrap); the account pages call the JSON API with JavaScript | Fewer external dependencies. | Same screens as SAD 4.5. |
| D-13 | Document endpoints | `POST /documents`, `GET /documents`, `PUT /documents/{id}`, `GET /admin/documents?status=Pending`, `PUT /admin/documents/{id}/review` | `GET/POST /documents/upload`, `GET /documents`, `POST /documents/<id>/resubmit`, `GET /admin/documents` and `/admin/documents.json`, `POST /admin/documents/<id>/review`, `GET /admin/documents/<id>/file`. Upload, resubmission and review forms carry a form token. Uploads are stored in `instance/uploads/` under random names; PDF and image contents are checked, not just the extension. | HTML forms use POST; the file view and the content checks were added for safety. | Same behaviour as SAD 4.3.3 (415 and 413 become a form error with 400). This also partly answers D-03: the document forms have a CSRF token. |
| D-14 | Catalogue endpoints | `GET /colleges?search=`, `POST/PUT /admin/colleges`, `/admin/colleges/{id}/branches`, `/admin/seat-matrix` (JSON) | `GET /colleges` with filters `q` and `college_id`; admin pages `/admin/colleges`, `/admin/colleges/new`, `/admin/colleges/<id>/edit`, `/admin/colleges/<id>/branches/new`, `/admin/branches/<id>/edit`, `/admin/branches/<id>/seats` (HTML forms). Duplicates return 409 and invalid capacity 422. Seat categories: General, OBC, SC, ST, EWS. | Server-rendered admin screens fit the Flask design. | Same rules as ADM-F-010 and ADM-F-011. The admin pages use the shared `role_required("administrator")` check: 401 anonymous, 403 candidate. |
| D-15 | Eligibility | Rules as editable data, status with reason (ADM-F-009) | Pure decision function with `eligibility_rules` rows (category, cut-off rank, active). Order: Pending while documents are not all approved, Not Eligible if the rank is above the cut-off or no rule exists, otherwise Eligible. Cut-offs are fictional sample data. | SAD A-08 and A-06. | Rules are data, not code. Not yet connected to the real exam details and documents (section 3). |

## 3. Sprint One gaps: status on 1 November 2026

All six gaps open at the end of Sprint One were closed in the code on `main` (checked on 1 Nov, not just reported).

| # | Area | Gap on 21 October | Now |
|---|---|---|---|
| P-01 | Candidate exam details in the browser | Profile page had no exam-details form | Closed: `templates/accounts/profile.html` has the form; `PUT /accounts/exam-details` still accepts only a seeded combination |
| P-02 | Required documents | No `all_documents_approved`, any type text accepted, no foreign keys, no audit | Closed: `REQUIRED_DOCUMENT_TYPES` (Marksheet, ID Proof, Category Certificate), `all_documents_approved(candidate_id)`, foreign keys to `users` and `applications`, review writes an audit entry |
| P-03 | Eligibility connection | Sample inputs, no login | Closed: reads the real exam details and `all_documents_approved`; login required |
| P-04 | Catalogue admin access | Guard denied everyone | Closed: shared `role_required("administrator")` |
| P-05 | Audit log and admin dashboard | Not built | Closed: `audit_log` is append-only through database triggers (A-17); `/admin/audit-logs` and `/admin/dashboard` exist |
| P-06 | CSRF protection | Only document forms | Closed: every state-changing request (D-03) |
| P-07 | Test evidence | Ongoing | Each owner records results in `docs/evidence/`; a test case is marked passed only after it was run |

## 4. Out of Sprint One scope (by design, Sprint Two)

Choice filling, ordering and locking; seat allotment and Not Allocated; result publication and the accept/reject decision; performance and consistency testing; configuration screens (see `SPRINT_ONE_START_HERE.md`).

## 5. How we work (process notes)

- One feature branch per task, pull requests into `main`, a CI check (`.github/workflows/ci.yml`) runs the tests on every push and pull request.
- Fictional data only; no database file, upload, certificate, key or password is committed.
- Pull requests are raised by each module owner and reviewed and merged by the repo owner on GitHub. Some early merges (foundation, accounts, application) were done from the command line to unblock the team; their pull requests were closed as "already merged into main".

## 6. Sprint Two choices (30 October to 1 November 2026)

D-16 to D-18 were recorded when the choice, allotment and result tables were agreed (`SPRINT_TWO_START_HERE.md` section 4); D-19 to D-22 come from the built Sprint Two code. No requirement changed.

| # | Area | Submitted (SAD) | Built | Reason | Impact |
|---|---|---|---|---|---|
| D-16 | Where "published" is stored | SAD 4.1: the allotment run moves from Completed to Published | A separate `result_publications` table owned by the Result module, with a unique `run_id` | One owner per module; "publish once" becomes a database rule instead of a status the Allotment module would also have to change | ADM-F-017 behaves the same: results are hidden until the administrator publishes |
| D-17 | Paths and pages | `/api/v1/choices`, `/api/v1/admin/allotment/run`, `/api/v1/allotment/result` and so on | Exactly those API paths, plus HTML pages `/choices`, `/result`, `/admin/allotment` | The SAD defines the API only; the pages are the Flask screens in SAD 4.5 | No deviation, recorded for completeness |
| D-18 | Rules enforced by the database | A-07, A-13, ADM-NFR-003 describe the rules | `allotment_runs.cycle` is always 1 and unique (one cycle); run counts must add up; an `Allocated` result must have a branch, seat and choice number and a `Not Allocated` one must have none; `choices` refuses a branch twice per candidate; `seat_decisions` allows one row per result | Even a bug in application code cannot break these rules | Stricter than the SAD text, same intent |
| D-19 | Who takes part in the allotment run | SAD 4.1: every eligible candidate with a locked list gets Allocated or Not Allocated | Same, and eligibility and documents are checked again inside the run. A candidate who is not Eligible at run time, or never locked, gets **no result row** (decision D2-06), so "not in the run" is never shown as "Not Allocated" | A Not Allocated result would wrongly say the candidate competed for a seat | ADM-F-015 and ADM-F-016 are met; the candidate result page must show a separate message when there is no result row |
| D-20 | Submit needs exam details | ADM-F-005: submit when mandatory fields are complete | Also refused (422, "Enter your exam details first") while no exam details are saved (decision D2-02). Saving a draft still works | Eligibility and allotment need the rank and category; a submitted application without them could never be processed | Stricter than the SAD, same intent |
| D-21 | Admin rule, dashboard and audit endpoints | `POST/PUT /admin/eligibility-rules`, `GET /admin/dashboard`, `GET /admin/audit-logs` (JSON) | HTML pages `GET/POST /admin/eligibility-rules`, `POST /admin/eligibility-rules/<id>` (update as a form POST), `GET /admin/dashboard` and `/admin/dashboard.json`, `GET /admin/audit-logs` and `/admin/audit-logs.json` | HTML forms use POST; the `.json` variants keep the API shape | Same data and rules as SAD 4.3.4 and 4.3.7 |
| D-22 | Measured performance (ADM-NFR-002, ADM-NFR-003) | A run-time target and a consistency check after each run | `scripts/time_allotment.py`: 300 candidates median 0.967 s, 600 candidates median 1.589 s (limit 60 s). `scripts/check_seat_consistency.py` and the console tile show filled = allotment records for every seat row; the database refuses `filled > capacity` | (no deviation) | Evidence in `docs/evidence/gagan.md` |

## 7. Items open on Day 3 morning, closed the same day

All four were merged into `main` on 1 November 2026 and the full suite passed on the combined code (810 passed). Nothing from this list is left open at the `v1.0` tag.

| # | Area | Closed by | Notes |
|---|---|---|---|
| O-01 | Candidate result page and seat decision (ADM-F-018, ADM-F-019; issues #13, #14) | #77 (Dikshith) | `GET /result`, `GET /api/v1/allotment/result` (404 until published), `POST /api/v1/allotment/decision` with `{decision: Accept or Reject}`, `POST /result/decision`. A candidate who was not in the run sees a separate message (D-19). One decision per result is a database rule; a rejected seat is not released (SAD open issue 5). The API answers 201 on a recorded decision where SAD 4.3.6 says 200; the body is as designed |
| O-02 | Administrator candidate list (ADM-F-020) | #78 (Tasya) | `GET /admin/candidates` |
| O-03 | Response-time measurement (ADM-NFR-001, TC-026) | #78 (Tasya) | `docs/evidence/tasya-response-time.md`: averages 3 to 16 ms on the tested candidate pages, target 2 s; single client, not a load test |
| O-04 | Candidate dashboard with journey steps | #76 and #79 (Varun) | `GET /dashboard` with the seven journey steps (`GET /accounts/dashboard` is the older JSON identity endpoint); #79 shows the real approved-document count (DEF-012) |
