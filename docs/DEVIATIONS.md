# Deviations from the submitted SRS, SAD and Test Plan

Status date: **24 October 2026** (end of Sprint One). This file records every place where the product differs from the documents we submitted, why, and what we will say in the final demo. The SRS stays authoritative: **no functional or security requirement was dropped or changed**; the differences below are design and implementation choices. Section 3 lists what is still open; everything that was open during the sprint is listed as resolved. `python -m pytest -q` (455 tests at the time of writing) and `tests/integration/test_demo_flow.py` are the regression checks.

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
| D-16 | Audit log | Entries hold actor, timestamp, action type, target id and outcome; append-only through database triggers; read-only administrator view (SEC-F-005, A-17) | As designed: `audit_log` table, triggers reject UPDATE and DELETE, `GET /admin/audit-logs` (page) and `/admin/audit-logs.json`. Entries hold ids and the decision, never a rejection reason or file name. The entry is committed right after the action, **not in the same database transaction**. | Simplest way to call it from every module. | An action could be saved without its audit entry if the second commit failed. Planned improvement for Sprint Two. |
| D-17 | Administrator dashboard | `GET /admin/dashboard` with counts and pending queues (ADM-F-020) | `GET /admin/dashboard` (page) and `/admin/dashboard.json`: candidate counts, application and document status counts, pending documents. | (no deviation) | Same as SAD 4.3.7. |
| D-18 | Database upgrade | Not in the SAD | `flask --app app upgrade-document-references` adds the document foreign keys to an existing SQLite file without losing rows. Never runs automatically. | Teammates already had local databases. | Tooling only. |

## 3. Open at the end of Sprint One

| # | Area | What is open | Owner |
|---|---|---|---|
| P-06 | CSRF protection | Only the document forms carry a token. The accounts, application, catalogue and eligibility forms and the JSON endpoints rely on `SameSite=Lax` cookies. Planned for Sprint Two. | Team |
| P-08 | Audit entry is not in the same transaction as the action | See D-16. | Tasya |
| P-09 | Registration does not collect date of birth | See D-05. | Varun |
| P-10 | Peer reviews | Several early pull requests were merged by their authors; from 21 October the repo owner merged pull requests through GitHub. | Team |

### Resolved during Sprint One

Candidate exam details form on the profile page; `all_documents_approved()` and the required document types; uploads restricted to Marksheet, ID Proof and Category Certificate; documents linked to users and applications by foreign keys; eligibility on real exam details and approvals and behind login; catalogue administration for the administrator account; administrator dashboard; audit log; test evidence files (`docs/evidence/gagan.md`, `varun.md`, `dikshith.md`; Tasya's file to follow).

## 4. Out of Sprint One scope (by design, Sprint Two)

Choice filling, ordering and locking; seat allotment and Not Allocated; result publication and the accept/reject decision; performance and consistency testing; configuration screens (see `SPRINT_ONE_START_HERE.md`).

## 5. How we work (process notes)

- One feature branch per task, pull requests into `main`, a CI check (`.github/workflows/ci.yml`) runs the tests on every push and pull request.
- Fictional data only; no database file, upload, certificate, key or password is committed.
- Pull requests are raised by each module owner and reviewed and merged by the repo owner on GitHub. Some early merges (foundation, accounts, application) were done from the command line to unblock the team; their pull requests were closed as "already merged into main".
