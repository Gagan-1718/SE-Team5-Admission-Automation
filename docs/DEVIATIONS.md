# Deviations from the submitted SRS, SAD and Test Plan

Status date: **20 October 2026** (Sprint One, day 2). This file records every place where the product differs from the documents we submitted, why, and what we will say in the final demo. The SRS stays authoritative: **no functional or security requirement was dropped or changed**; the differences below are design and implementation choices. Items marked *Pending* will be completed when the owner's module is merged.

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

## 3. Pending: will be completed or documented when merged

| # | Area | What to confirm |
|---|---|---|
| P-01 | Documents module (Dikshith) | Final endpoint paths versus SAD 4.3.3; document type list (Marksheet, ID Proof, Category Certificate, proposed); resubmission replaces the stored file and resets to Pending. |
| P-02 | Catalogue (Tasya) | Endpoint paths versus SAD 4.3.4; seat categories General, OBC, SC, ST, EWS. |
| P-03 | Eligibility, audit log, admin dashboard (Tasya) | Cut-off rules are fictional sample data (rank limits per category), editable data, not hard-coded. Audit log: append-only through database triggers, as in SAD A-17. |
| P-04 | Test evidence | Results recorded in `docs/evidence/` by each owner. A test case is only marked passed after it was run. |

## 4. Out of Sprint One scope (by design, Sprint Two)

Choice filling, ordering and locking; seat allotment and Not Allocated; result publication and the accept/reject decision; performance and consistency testing; configuration screens (see `SPRINT_ONE_START_HERE.md`).

## 5. How we work (process notes)

- One feature branch per task, pull requests into `main`, a CI check (`.github/workflows/ci.yml`) runs the tests on every push and pull request.
- Fictional data only; no database file, upload, certificate, key or password is committed.
- Pull requests are raised by each module owner and reviewed and merged by the repo owner on GitHub. Some early merges (foundation, accounts, application) were done from the command line to unblock the team; their pull requests were closed as "already merged into main".
