# Updated Test Plan and Test Case Document - Part 3

Project: Team 5 Admission Automation  
Revision: 2.0 - 8 November 2026  
Scope: Original TC-001 through TC-030; 20 functional, five security and five non-functional requirements.

## 1. Baseline and purpose

This is the final-implementation revision to the original [Test Plan](../../TestPlan_Team5_Admission_Automation.pdf), read with the [Python Test Plan Addendum](../../TEST_PLAN_PYTHON_ADDENDUM.md), [Python SAD](../../SAD_Python.md) and [recorded deviations](../DEVIATIONS.md). Original IDs and the Appendix B oracle are retained. The original PDF is preserved. This document supplies updated procedures, expected results, execution references and honest actual-result notes; it is not a substitute for the unit/system/coverage reports.

The main changes are Python/Flask/SQLite, real sessions and permissions, matched exam details, a submitted-application prerequisite for uploads, three required private document types, approval/rejection/resubmission, data-driven eligibility/catalogue, choices and locking, atomic single-cycle allotment, publication, private results, one-time decisions and append-only audit. Minimum age is a supplementary registration input check, not the focus of this revision.

## 2. Test environment and data

- Windows, Python 3.12.10, pytest and Flask test client; SQLAlchemy and isolated temporary SQLite databases with foreign keys enabled. Fictional records and generated PDF/JPEG/PNG files only.
- Separate candidate/admin sessions; seeded exam tuples such as KCET / rank 1000 / General / score 185.0. Nonmatching tuples are rejected.
- Application submission requires exam details and guardian_name, guardian_mobile, school_name, board and percentage. Submitted data is locked and has a unique ADM-YYYY-NNNNNN reference.
- Required documents: Marksheet, ID Proof, Category Certificate; file types PDF/JPEG/PNG and limit 2 MiB. Content/structure, identity and ownership are validated. Internal Pending corresponds to Pending Verification.
- Native forms and JSON APIs have different response contracts: candidate page redirects, API/admin 401, candidate admin access 403, validation/CSRF 400, conflicts 409 and business validation 422 where implemented. Missing CSRF on unsafe requests can be rejected before role checks.
- Normal TESTING mode disables central CSRF; dedicated security and oracle result/decision HTTP tests enable it. Server-rendered HTML assertions do not execute an actual browser. HTTPS uses optional requirements-https.txt and temporary localhost certificates/sockets.

## 3. Current execution evidence

| Ref | Command / source | Actual result |
|---|---|---|
| R1 | `python -m coverage run --branch --source=app -m pytest -q` | Owner terminal: **883 passed, 1 skipped in 499.26s**. HTTPS module skipped for missing optional dependencies. |
| R2 | `python -m coverage run --append --branch --source=app -m pytest tests/test_https.py -q -rs` | Owner terminal: **10 passed in 27.96s**, after dependencies were installed. |
| R3 | [coverage.json](reports/coverage.json), exported 8 November 2026 | **95.46% statement coverage; 89.74% branch coverage**, merging R1/R2. |
| R4 | Dikshith's confirmation | Usability good, personally verified through an owner walkthrough. No participant counts/timings or five-user session records were supplied. |
| Historical | Existing [individual evidence](../evidence/) | Earlier module/performance observations retain their original date, build and limitations. |

R1 and R2 are separate executions, not one full-suite run with 893 passes. Their results were supplied by the owner; per-test JUnit output was not supplied for these runs. The case mappings identify included scripts, not separate per-TC counts or faculty sign-off. No new test execution is claimed by creating this document.

Local HEAD inspected when preparing the coverage reports was d3eb5cdc1d18bc0fd4b51b27803529b4ce35f15a. Execution-time SHA/working-tree state were not separately recorded. Record both for future runs.

## 4. Case index

| Case | Requirement | Area | Owner |
|---|---|---|---|

| TC-001 | ADM-F-001 | Candidate registration | Varun |
| TC-002 | ADM-F-002 | Login and logout | Varun |
| TC-003 | ADM-F-003 | Profile and exam details | Varun |
| TC-004 | ADM-F-004 | Save and resume draft | Gagan |
| TC-005 | ADM-F-005 | Submit and reference | Gagan |
| TC-006 | ADM-F-006 | Upload validation and storage | Dikshith |
| TC-007 | ADM-F-007 | Approve or reject documents | Dikshith |
| TC-008 | ADM-F-008 | Status and resubmission | Dikshith |
| TC-009 | ADM-F-009 | Eligibility status and reason | Tasya |
| TC-010 | ADM-F-010 | Catalogue and available seats | Tasya |
| TC-011 | ADM-F-011 | Administrator catalogue and seats | Tasya |
| TC-012 | ADM-F-012 | Add remove preview choices | Varun |
| TC-013 | ADM-F-013 | Reorder choices | Varun |
| TC-014 | ADM-F-014 | Lock choice list | Varun |
| TC-015 | ADM-F-015 | Rank and preference allotment | Gagan |
| TC-016 | ADM-F-016 | Not Allocated outcome | Gagan |
| TC-017 | ADM-F-017 | Publish completed results | Dikshith |
| TC-018 | ADM-F-018 | Private result and letter | Dikshith |
| TC-019 | ADM-F-019 | Exactly-once accept/reject | Dikshith |
| TC-020 | ADM-F-020 | Admin dashboard and records | Tasya |
| TC-021 | SEC-F-001 | Mandatory authentication | Varun |
| TC-022 | SEC-F-002 | Administrator role enforcement | Dikshith |
| TC-023 | SEC-F-003 | Salted password hashes | Varun |
| TC-024 | SEC-F-004 | TLS and encrypted credentials | Gagan |
| TC-025 | SEC-F-005 | Append-only audit | Tasya |
| TC-026 | ADM-NFR-001 | Candidate response time | Tasya |
| TC-027 | ADM-NFR-002 | Allotment performance | Gagan |
| TC-028 | ADM-NFR-003 | Seat consistency and capacity | Gagan |
| TC-029 | ADM-NFR-004 | First-time-user usability | Dikshith |
| TC-030 | ADM-NFR-005 | Configuration without code changes | Tasya |

## 5. Updated test cases

### TC-001 - Candidate registration

**Requirement:** ADM-F-001  
**Owner:** Varun

**Preconditions / data:** No existing candidate; fictional unique email/mobile and past DOB.

**Steps:**

1. Register valid data.
2. repeat email and mobile.
3. omit or corrupt mandatory fields and DOB. Also check the supplementary age boundary: exactly sixteen accepted, one day younger rejected.

**Expected result:** Valid registration 201; duplicates 409; invalid input rejected; stored password is a hash.

**Final implementation update:** Required DOB, strict text/length validation and normalized email; minimum age sixteen is an additional input validation. Other registration behavior remains part of the original case.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/accounts/test_registration.py tests/accounts/test_registration_validation.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-002 - Login and logout

**Requirement:** ADM-F-002  
**Owner:** Varun

**Preconditions / data:** Registered candidate and seeded administrator.

**Steps:**

1. Try wrong and correct credentials.
2. log out.
3. reuse the old session cookie.

**Expected result:** Wrong credentials 401; valid login succeeds; logout invalidates the server-side session.

**Final implementation update:** Use /accounts/login and /accounts/logout; no recoverable plaintext password.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/accounts/test_login_logout.py tests/accounts/test_integration.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-003 - Profile and exam details

**Requirement:** ADM-F-003  
**Owner:** Varun

**Preconditions / data:** Logged-in candidate; seeded KCET/COMEDK exam records.

**Steps:**

1. Read/update owned profile.
2. enter matching and nonmatching exam combinations.
3. attempt changes after submission and identity spoofing.

**Expected result:** Matching exam details saved; mismatch 422 no_matching_record; exam details locked after submission; other records inaccessible.

**Final implementation update:** PUT /accounts/exam-details; seeded tuple required; rank/category not arbitrary.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/accounts/test_profile.py tests/accounts/test_exam_details.py tests/accounts/test_profile_integrity.py tests/accounts/test_profile_exam_form.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-004 - Save and resume draft

**Requirement:** ADM-F-004  
**Owner:** Gagan

**Preconditions / data:** Candidate login; no submitted application.

**Steps:**

1. Save partial draft.
2. log out/in.
3. resume and edit.
4. try another candidate's application.

**Expected result:** Draft values persist; no reference until submission; unauthorized access refused.

**Final implementation update:** Draft may exist before exam details; native page /application.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/application/test_draft.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-005 - Submit and reference

**Requirement:** ADM-F-005  
**Owner:** Gagan

**Preconditions / data:** Candidate with matching exam details and required application fields.

**Steps:**

1. Submit incomplete data, then complete data.
2. repeat submission.
3. compare two candidates' references and stale submission behavior.

**Expected result:** Missing fields or exam details 422; successful submission locks data and gives unique ADM-YYYY-NNNNNN; repeat 409.

**Final implementation update:** Mandatory guardian_name, guardian_mobile, school_name, board, percentage; exam details prerequisite.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/application/test_submit.py tests/application/test_exam_details_required.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-006 - Upload validation and storage

**Requirement:** ADM-F-006  
**Owner:** Dikshith

**Preconditions / data:** Authenticated candidate with submitted application; temporary upload storage.

**Steps:**

1. Upload PDF/JPEG/PNG for each allowed type.
2. test empty, forged, damaged, oversized and unsupported uploads.

**Expected result:** Valid private file and Pending metadata saved; invalid uploads 400; no partial file/row; candidate/application foreign keys enforced.

**Final implementation update:** Limit 2 MiB; types exactly Marksheet, ID Proof, Category Certificate; /documents/upload.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/documents/test_validation.py tests/documents/test_routes.py tests/documents/test_services.py tests/documents/test_models.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-007 - Approve or reject documents

**Requirement:** ADM-F-007  
**Owner:** Dikshith

**Preconditions / data:** Pending documents and logged-in administrator.

**Steps:**

1. Approve one.
2. reject another without then with reason.
3. repeat review.
4. attempt candidate review.
5. inspect audit.

**Expected result:** Valid decisions persist; reason mandatory for rejection (422 if absent); repeat conflict; unauthorized users denied; audit recorded.

**Final implementation update:** POST /admin/documents/<id>/review; HTML queue separate from .json list.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/documents/test_review_routes.py tests/documents/test_review_services.py tests/audit/test_document_review_audit.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-008 - Status and resubmission

**Requirement:** ADM-F-008  
**Owner:** Dikshith

**Preconditions / data:** Owned rejected and approved documents.

**Steps:**

1. Read rejection reason.
2. replace rejected file.
3. inspect Pending state.
4. attempt approved/other-user replacement.
5. simulate storage failure.

**Expected result:** Replacement only for owned Rejected document; Pending reset; original retained on failure; status/reason visible only to owner.

**Final implementation update:** POST /documents/<id>/resubmit; private storage and central CSRF.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/documents/test_status.py tests/documents/test_resubmission_routes.py tests/documents/test_resubmission_services.py tests/documents/test_replacement_storage.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-009 - Eligibility status and reason

**Requirement:** ADM-F-009  
**Owner:** Tasya

**Preconditions / data:** Exam details, editable rules, candidates with missing/pending/approved required documents.

**Steps:**

1. Check missing exam/documents.
2. boundary rank.
3. above cutoff.
4. unknown/inactive rule and fully eligible case.

**Expected result:** Pending until all required documents approved; Eligible at cutoff; Not Eligible above cutoff or absent rule; readable reason.

**Final implementation update:** Internal Pending equals submitted Pending Verification; real identity and documents used.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/eligibility/test_evaluate.py tests/eligibility/test_routes.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-010 - Catalogue and available seats

**Requirement:** ADM-F-010  
**Owner:** Tasya

**Preconditions / data:** Seeded colleges, branches and category seat rows.

**Steps:**

1. Browse.
2. filter by college/branch term and college ID.
3. use no-match query.
4. compare availability with seat data.

**Expected result:** Only matches displayed; empty result handled; availability equals capacity minus filled.

**Final implementation update:** GET /colleges uses q and college_id filters.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/catalogue/test_candidate.py tests/catalogue/test_models.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-011 - Administrator catalogue and seats

**Requirement:** ADM-F-011  
**Owner:** Tasya

**Preconditions / data:** Admin login, existing and new college/branch, candidate account.

**Steps:**

1. Create/edit college and branch.
2. change category capacities.
3. try duplicates, invalid capacity and capacity below filled.
4. inspect candidate catalogue.

**Expected result:** Admin changes persist and flow to candidate views; invalid/duplicate changes refused; constraints prevent overcapacity.

**Final implementation update:** Native forms under /admin/colleges and /admin/branches; shared role guard.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/catalogue/test_admin.py tests/catalogue/test_models.py tests/integration/test_demo_flow.py::test_admin_configured_catalogue_flows_through_choices_and_allotment
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-012 - Add remove preview choices

**Requirement:** ADM-F-012  
**Owner:** Varun

**Preconditions / data:** Eligible candidate with approved documents and unlocked list.

**Steps:**

1. Add choices.
2. list/preview.
3. remove.
4. try duplicate and ineligible candidate.

**Expected result:** Ordered list persists; duplicate rejected; removal reflected; ineligible candidate cannot change choices.

**Final implementation update:** HTML /choices and /api/v1/choices.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/choices/test_add.py tests/choices/test_remove.py tests/choices/test_listing.py tests/choices/test_page.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-013 - Reorder choices

**Requirement:** ADM-F-013  
**Owner:** Varun

**Preconditions / data:** At least three owned unlocked choices.

**Steps:**

1. Move third to first.
2. reload list.
3. try missing/duplicate/other-user IDs and invalid order.

**Expected result:** Valid order persists; malformed or foreign order rejected atomically.

**Final implementation update:** Use agreed API payload; real browser re-login verification remains a manual supplement.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/choices/test_reorder.py tests/choices/test_routes.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-014 - Lock choice list

**Requirement:** ADM-F-014  
**Owner:** Varun

**Preconditions / data:** Eligible candidate with nonempty ordered list.

**Steps:**

1. Lock.
2. attempt add/remove/reorder.
3. repeat lock.
4. test empty/ineligible list.

**Expected result:** Frozen list used for allotment; further mutation refused; invalid locks rejected.

**Final implementation update:** Single-cycle list is immutable after lock.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/choices/test_lock.py tests/choices/test_services.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-015 - Rank and preference allotment

**Requirement:** ADM-F-015  
**Owner:** Gagan

**Preconditions / data:** Appendix B oracle; locked eligible candidates and category seat rows.

**Steps:**

1. Run shuffled oracle.
2. test rank order, ties, preferences, categories, skipped ineligible/unlocked candidate, concurrency and rollback.

**Expected result:** C1/C2 A-CSE, C3 A-ISE; own category only; exactly one completed run; no partial seats/results on failure.

**Final implementation update:** SQLite write transaction before read/update; original oracle unchanged.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/allotment/test_engine.py tests/allotment/test_run_service.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-016 - Not Allocated outcome

**Requirement:** ADM-F-016  
**Owner:** Gagan

**Preconditions / data:** Appendix B C4/C5 exhaust all locked preferences.

**Steps:**

1. Run oracle and inspect result rows.
2. distinguish candidate never in run.

**Expected result:** C4/C5 Not Allocated with no college/branch; nonparticipant has no result row, distinct NOT_IN_RUN.

**Final implementation update:** Not Allocated does not mean never locked or otherwise excluded.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/allotment/test_engine.py tests/allotment/test_run_service.py tests/results/test_candidate_result.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-017 - Publish completed results

**Requirement:** ADM-F-017  
**Owner:** Dikshith

**Preconditions / data:** Completed consistent run, initially unpublished; admin and candidate logins.

**Steps:**

1. Read before publication.
2. publish in console/API.
3. read again.
4. repeat, unauthorized or unknown-run publication.
5. simulate audit failure.

**Expected result:** No allocation disclosed before publish; publication exposes owned result; success API 201, unknown 404, duplicate 409; atomic publication/audit.

**Final implementation update:** Separate result_publications table; POST /api/v1/admin/allotment/runs/<id>/publish.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/results/test_publication_service.py tests/results/test_publication_routes.py tests/results/test_publish_card.py tests/allotment/test_result_decision_flow.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-018 - Private result and letter

**Requirement:** ADM-F-018  
**Owner:** Dikshith

**Preconditions / data:** Published allocated/unallocated results and nonparticipant.

**Steps:**

1. Open /result and API as each candidate.
2. spoof query IDs.
3. inspect letter fields, escaping and print CSS.

**Expected result:** Owned allocation fields correct; unallocated has no college; NOT_IN_RUN separate; no cross-user disclosure; private/no-store responses.

**Final implementation update:** API 404 until publication; actual browser print pagination still manual.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/results/test_candidate_result.py tests/allotment/test_result_decision_flow.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions. Browser print-preview/pagination is not established by a stylesheet assertion.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-019 - Exactly-once accept/reject

**Requirement:** ADM-F-019  
**Owner:** Dikshith

**Preconditions / data:** Published allocated seats for two candidates.

**Steps:**

1. Accept A and reject B.
2. retry/change.
3. race two sessions.
4. attempt before publication/no seat.
5. simulate audit/commit failure.

**Expected result:** One Accepted/Rejected row and audit; success 201, repeat 409, no seat 422; failed transaction rolled back; seat counts unchanged.

**Final implementation update:** API sends Accept/Reject; stores Accepted/Rejected; rejection never releases/reallots seat.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/results/test_seat_decision.py tests/results/test_result_models.py tests/allotment/test_result_decision_flow.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-020 - Admin dashboard and records

**Requirement:** ADM-F-020  
**Owner:** Tasya

**Preconditions / data:** Applications/documents/candidates in multiple states.

**Steps:**

1. Compare dashboard counts/queues with DB.
2. search, paginate and view candidate records; validate access control.
3. confirm that direct administrator editing remains out of approved D-23 scope.

**Expected result:** Dashboard totals, search results, pagination, and read-only record views match the database; candidate-role access is denied; direct record editing is explicitly excluded from scope under D-23 and is not treated as an open defect.

**Final implementation update:** The approved D-23 scope covers administrator viewing, searching, pagination, dashboard checks, and access control only; direct candidate record editing is outside scope.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/admin
```

**Actual result / evidence:** Dashboard counts/search/pagination and access-control checks passed as part of R1. Direct candidate record editing remains explicitly outside the approved D-23 scope and is not an open defect.

**Status:** PASS for the approved D-23 read-only administration scope; direct editing is not in scope.

### TC-021 - Mandatory authentication

**Requirement:** SEC-F-001  
**Owner:** Varun

**Preconditions / data:** Anonymous client, candidate session and logged-out stale cookie.

**Steps:**

1. Discover protected pages/APIs.
2. attempt access anonymously and after logout.

**Expected result:** No protected data returned; browser candidate pages redirect, APIs/admin use 401; stale session invalid.

**Final implementation update:** Path-specific redirect/401 contract replaces blanket redirect expectation; unsafe missing-CSRF requests can fail 400 first.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/accounts/test_protected_routes.py tests/accounts/test_integration.py tests/application/test_identity.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-022 - Administrator role enforcement

**Requirement:** SEC-F-002  
**Owner:** Dikshith

**Preconditions / data:** Anonymous, candidate and administrator clients; real route IDs.

**Steps:**

1. Call every current admin GET and write route.
2. compare state before/after denial.
3. test successful authorized paths.

**Expected result:** Candidate 403; anonymous 401 where specified; no unauthorized state/audit changes; admin paths available.

**Final implementation update:** Shared role_required guard; CSRF enforced separately, does not replace role checks.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/security/test_admin_authorization.py tests/catalogue/test_admin.py tests/results/test_publication_routes.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-023 - Salted password hashes

**Requirement:** SEC-F-003  
**Owner:** Varun

**Preconditions / data:** Two registrations with same fictional password and credential store access.

**Steps:**

1. Compare hashes.
2. verify correct/wrong password.
3. test malformed hash.
4. inspect stored representation.

**Expected result:** Different salted scrypt hashes; correct verification only; no plaintext password in stored hash.

**Final implementation update:** Werkzeug scrypt replaces illustrative BCrypt; broad production log review not claimed.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/accounts/test_password_hashing.py tests/accounts/test_integration.py::test_users_store_only_password_hashes
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions. Controlled application-log inspection for fictional passwords is not separately recorded.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-024 - TLS and encrypted credentials

**Requirement:** SEC-F-004  
**Owner:** Gagan

**Preconditions / data:** Cheroot/cryptography installed; temporary localhost certificate and real socket permission.

**Steps:**

1. Negotiate TLS.
2. inspect capture for password/email.
3. plain-HTTP control.
4. redirect, secure cookie and untrusted-cert checks.

**Expected result:** TLS >=1.2; no plaintext credentials in TLS bytes; HTTP redirected/refused; capture control works; certificate trust behavior correct.

**Final implementation update:** Self-signed localhost certificate is a lab setup, not publicly trusted deployment.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/test_https.py tests/test_security_headers.py
```

**Actual result / evidence:** All ten HTTPS tests passed after installing optional dependencies. Their coverage was appended. UNKNOWN_CA output accompanies the deliberate untrusted-certificate check; it is not a pytest failure.

**Status:** PASS for automated HTTPS scope in R2; initial R1 module skip retained historically.

### TC-025 - Append-only audit

**Requirement:** SEC-F-005  
**Owner:** Tasya

**Preconditions / data:** Admin seat/document/allotment/publication actions and candidate decisions.

**Steps:**

1. Inspect actor/time/action entries.
2. filter log.
3. try HTTP mutation and direct DB UPDATE/DELETE.
4. test audit atomic rollback.

**Expected result:** Expected actions recorded; HTTP mutation unavailable; DB triggers reject changes; related business/audit writes atomic.

**Final implementation update:** SQLite trigger protection is not protection from an operator with filesystem access.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/audit tests/allotment/test_result_decision_flow.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.
**Execution reference:** [Tasya Sprint 2 evidence](../evidence/tasya.md), Section 4.1 (TC-025).
**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-026 - Candidate response time

**Requirement:** ADM-NFR-001  
**Owner:** Tasya

**Preconditions / data:** Documented demo environment and seeded accounts.

**Steps:**

1. Repeat login/catalogue/eligibility/choices requests.
2. retain response codes and timing.
3. run proposed 25 concurrent users if retained by team.

**Expected result:** Mean standard response <=2s under stated workload; report concurrent work separately from sequential request timings.

**Final implementation update:** Sequential single-client measurements are retained as historical evidence. A separate 25-concurrent-candidate workload was executed and is documented below.

**Execution reference:** [Tasya response-time evidence](../evidence/tasya-response-time.md).

**Actual result / evidence:** Sequential measurements recorded on 1 November 2026: login 3.42 ms, catalogue 7.55 ms, eligibility 10.60 ms and choices 15.46 ms (average response times; single client).

A separate concurrent test was recorded on 13 November 2026 using 25 candidate sessions and an isolated dataset of 300 fictional candidates. It measured 25 requests per endpoint (100 requests total):

- Sign-in: average 443.31 ms; P95 831.18 ms; maximum 925.23 ms.
- Dashboard: average 524.89 ms; P95 725.94 ms; maximum 787.60 ms.
- Catalogue: average 387.35 ms; P95 558.97 ms; maximum 560.27 ms.
- Choices: average 331.28 ms; P95 418.12 ms; maximum 444.83 ms.

All 100 requests returned HTTP 200. All measured average and P95 response times were below the 2-second target. The sequential and concurrent measurements are separate test runs. The concurrent test used a local Flask development server and does not establish production performance.

**Status:** PASS for the recorded 25-concurrent-candidate workload in the local demo environment. Production performance is not established.

### TC-027 - Allotment performance

**Requirement:** ADM-NFR-002  
**Owner:** Gagan

**Preconditions / data:** Disposable seeded datasets of 300 and 600 candidates.

**Steps:**

1. Run time_allotment.py --candidates 300 then 600, three timed runs each.
2. retain counts/timings/machine and consistency.

**Expected result:** Every timed allotment <60s; double dataset needs no code changes; deterministic counts and no seat mismatches.

**Final implementation update:** Timed service phase excludes dataset construction; report dataset total and eligible+locked participants separately.

**Repeat commands (not executed by creating this document):**

```powershell
python scripts/time_allotment.py --candidates 300 --runs 3
python scripts/time_allotment.py --candidates 600 --runs 3
```

**Historical reference:** [Gagan evidence](../evidence/gagan.md).

**Actual result / evidence:** Gagan recorded three runs each for 300 and 600 candidates: medians 0.967 s and 1.589 s under the 60-second limit in his earlier documented environment. These are historical measurements; R1 small timing-script regression tests do not rerun the full scale benchmark.

**Status:** Historical scale measurement available; R1 timing-script checks are separate regression evidence.

### TC-028 - Seat consistency and capacity

**Requirement:** ADM-NFR-003  
**Owner:** Gagan

**Preconditions / data:** Completed oracle/scale run and configured category seats.

**Steps:**

1. Compare filled with result-row counts and capacity.
2. detect deliberate mismatch.
3. try overcapacity and second run.

**Expected result:** filled equals allocated rows; available=capacity-filled; no overcapacity; mismatch detected; second run refused.

**Final implementation update:** Rejected candidate decision does not decrement filled in the single-cycle model.

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/allotment/test_consistency_script.py tests/allotment/test_run_service.py tests/catalogue/test_models.py
```

**Actual result / evidence:** Relevant mapped tests are included in the owner-reported successful R1 suite. Individual per-case counts were not retained; manual substeps are not inferred from automated assertions.

**Status:** PASS for mapped automated scope (R1); requirement acceptance subject to owner review.

### TC-029 - First-time-user usability

**Requirement:** ADM-NFR-004  
**Owner:** Dikshith

**Preconditions / data:** Five first-time non-team users; final browser build and neutral script.

**Steps:**

1. Ask the owner to perform the candidate application walkthrough and record observed difficulties.
2. for the original first-time-user protocol, retain participant completion without help, elapsed time and assistance observations when conducted.

**Expected result:** At least 3/5 submit without external help; actual observations retained; no fabricated participants/results.

**Final implementation update:** Owner verification is now recorded. Preserve the original protocol if required for formal acceptance; do not mislabel personal verification as a five-person study.

**Execution reference:** Owner walkthrough (R4); participant-session records, if available, are separate human evidence.

**Actual result / evidence:** Dikshith confirmed usability is good and personally verified. Record this as owner verification. No five-participant identities, 3/5 result, times or assistance counts are invented. The original first-time-user criterion is distinct from a developer walkthrough.

**Status:** Usability verified by owner walkthrough (R4); original participant protocol not independently evidenced.

### TC-030 - Configuration without code changes

**Requirement:** ADM-NFR-005  
**Owner:** Tasya

**Preconditions / data:** Admin/candidate accounts; fictional college/branch/seat and eligibility rules.

**Steps:**

1. Add college/branch/capacity via admin.
2. update existing cutoff.
3. confirm candidate catalogue, eligibility, choices and allotment use new data.
4. separately create a new rule.

**Expected result:** New configured data applied without code change; permission protection holds; creating a new eligibility rule requires separate recorded execution.

**Final implementation update:** Existing pytest scenario updates a rule. The separate supplementary harness in the earlier isolated review package is not claimed as executed in folder (11).

**Mapped checks / repeat command:**

```powershell
python -m pytest -q tests/integration/test_demo_flow.py::test_admin_configured_catalogue_flows_through_choices_and_allotment
```

**Actual result / evidence:** Mapped integration creates college/branch/seats, updates an existing cutoff, and verifies catalogue, eligibility, choices and allotment. Creation of a rule for a previously absent category is a separate scenario, not proved by that cutoff update. Review full evidence before changing the older summary pending status.

**Execution reference:** [Tasya Sprint 2 evidence](../evidence/tasya.md), Section 4.3 (TC-030).

**Status:** PASS for existing integrated configuration scenario in R1; new-rule creation needs separate acceptance evidence.

## 6. Cross-module and supplementary checks

- Registration to documents, resubmission, eligibility and catalogue: tests/integration/test_demo_flow.py::test_full_demo_flow.
- Configuration to choices/allotment: tests/integration/test_demo_flow.py::test_admin_configured_catalogue_flows_through_choices_and_allotment.
- Oracle through run, publication, result and decisions: tests/allotment/test_result_decision_flow.py, central CSRF enabled.
- Application/document integration: tests/integration/test_admission_documents.py.
- Central CSRF, form tokens and same-origin fetch: tests/security/test_csrf.py and tests/security/test_csrf_fetch.py. These extend security validation without inventing a new SRS requirement ID.

Passing connected segments is not evidence of a single continuously observed browser run. Record actual browser registration-to-decision, mobile/keyboard and print-preview checks separately with date, build, browser and actual outcome.

## 7. Appendix B - unchanged oracle

General seats before allotment: A-CSE 2, A-ISE 1, B-ECE 1. All candidates eligible and lists locked; process ascending rank.

| Candidate | Rank | Locked choices | Expected |
|---|---:|---|---|
| C1 | 1 | A-CSE, A-ISE | A-CSE (Allocated) |
| C2 | 2 | A-CSE, B-ECE | A-CSE (Allocated) |
| C3 | 3 | A-CSE, A-ISE | A-ISE (Allocated) |
| C4 | 4 | A-CSE, A-ISE | Not Allocated |
| C5 | 5 | A-CSE | Not Allocated |

Remaining seats: A-CSE 0, A-ISE 0, B-ECE 1. Summary: five processed, three allocated, two Not Allocated. Additional category/ineligible scenarios extend rather than change the oracle.

## 8. Review and sign-off

- Keep original exit criteria: planned cases executed with evidence, oracle passing, requirements covered, defects triaged and no open Critical/High defects. Owner walkthrough verification does not itself grant faculty acceptance.
- Tasya consolidates reviewed per-requirement statuses in the RTM and system/summary reports. Do not mark every row Verified solely because pytest passed.
- Retain the dated older 820-pass summary and add a dated Part 3 update with R1/R2 and the final merged coverage. Do not overwrite historical dates/environments.
- Review the approved D-23 scope for TC-020, the local development-server limitation for TC-026, the participant-evidence limitation for TC-029, and the outstanding new-rule creation evidence for TC-030.
- Each module owner reviews their case details and adds actual dated evidence to their own file. Record real new defects and their agreed disposition in docs/DEFECT_LOG.md.
- This revision does not modify application code, the original PDF, existing coverage reports, commits or GitHub.
