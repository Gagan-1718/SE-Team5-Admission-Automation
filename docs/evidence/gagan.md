# Evidence: Gagan (20 October 2026)

Only results that were actually run are recorded here. Local laptop, Windows, Python 3.12.10, fictional data.

## TC-024 / SEC-F-004: HTTPS (issue #4)

**Command:** `python -m pytest -q tests/test_https.py`
**Observed:** 10 passed.

| Check | Observed |
|---|---|
| Page served over TLS with the generated certificate | `/health` returned 200 and `{"status":"ok","database":"ok"}`; negotiated version was TLS 1.2 or 1.3 |
| Certificate | self-signed, names `localhost` and `127.0.0.1`, currently valid |
| Client that does not trust the certificate | refused (`SSLCertVerificationError`; curl exit code 60) |
| Plain HTTP sent to the TLS port | no page is served |
| HTTP to HTTPS redirect | `http://localhost:8080/application?a=1` returned 301 to `https://localhost:8443/application?a=1` |
| Security headers over HTTPS | `Strict-Transport-Security: max-age=31536000`, `X-Content-Type-Options: nosniff` |
| Session cookie | `Set-Cookie` contains `Secure` and `HttpOnly` when served over HTTPS |
| Network capture | A relay recorded every byte between client and server while a candidate registered and logged in over HTTPS: the password, the email, `Set-Cookie` and the session cookie name were **not** present in the captured bytes |
| Control for the capture | The same recording over plain HTTP **does** contain the password and email, so the capture method works |

**Manual run of the real server** (`python scripts/serve_https.py`, then curl with `--cacert instance/certs/dev-cert.pem`):
`https://localhost:8443/health` gave 200 with HSTS and nosniff headers; without trusting the certificate curl failed with exit code 60; `http://localhost:8080/application?a=1` gave `301 https://localhost:8443/application?a=1`.

**Key handling:** `instance/certs/dev-key.pem` is created locally, is matched by `.gitignore` (`instance/`) and is not tracked by Git.

**Tests were checked to be able to fail:** with TLS disabled in `app/tls.py`, 6 of the 10 HTTPS tests failed; the file was then restored.

**Not done / limits:** no browser padlock screenshot has been taken yet (manual step); the certificate is self-signed and only valid for localhost; this is a lab setup, not an internet deployment.

## TC-004 / ADM-F-004: save and resume a draft (issue #2), with the real login

**Run:** `flask run` on the merged `main` code, requests made with curl and a cookie jar, using a registered fictional candidate.
**Observed:**
1. Anonymous `GET /application` -> 302 to `/accounts/login?next=/application`.
2. Register -> 201; login -> 200.
3. Partial draft saved -> 302 back to `/application`; the page then showed the saved guardian name.
4. After a server restart in the same browser session, the draft was still there; after logout the API returned 401; after logging in again the draft was still there.

Automated: `python -m pytest -q tests/application` -> 71 passed (includes `test_draft_survives_logout_and_login`).

## TC-005 / ADM-F-005: submit with a unique reference number (issue #3)

**Observed (same curl run):** submit with missing fields -> 422; submit with all fields -> 302 and the page showed `ADM-2026-000001`; a second submit -> 409. The database row held the logged-in user's id, status `Submitted` and that reference number.
Automated: `tests/application/test_submit.py` and `test_identity.py` pass.

## Integrated demo flow on `main` (21 October 2026)

**Run:** `python -m pytest -q tests/integration/test_demo_flow.py -rx` on `main` plus this test file, against a temporary database seeded exactly like `flask seed-db` (administrator, exam records, catalogue, eligibility rules). The test uses real routes, real logins and generated fictional files.

**Observed: 1 passed, 10 expected failures** (each one fails for exactly the reason written next to it; checked with `--runxfail`).

| Step | Result |
|---|---|
| Register, duplicate email refused (409), wrong password refused (401), login | PASS |
| Made-up rank refused (422); a seeded combination accepted (200) | PASS (TC-003) |
| Partial draft saved, logout, login, draft still there | PASS (TC-004) |
| Incomplete submit refused (422), complete submit gives `ADM-YYYY-NNNNNN`, second submit refused (409) | PASS (TC-005) |
| Wrong file type refused (400); Marksheet, ID Proof and Category Certificate uploaded | PASS (TC-006) |
| Administrator (seeded) sees the queue; rejecting without a reason refused (422); with a reason accepted and visible to the candidate | PASS (TC-007) |
| Candidate resubmits the rejected document; it returns to Pending; administrator approves; all three Approved | PASS (TC-008) |
| Eligibility endpoint returns a valid status and a reason | PASS for the shape only; the inputs are still sample values |
| Candidate browses the seeded catalogue | PASS (TC-010) |
| Candidate gets 403 on `/admin/documents`; anonymous visitors are redirected to login | PASS (TC-021, TC-022) |

**Not working yet (expected failures, owners in brackets):** the administrator cannot open `/admin/colleges` because the guard is not connected to the login (Tasya); eligibility always says Eligible, ignores the real exam details and is not login-protected (Tasya); `/admin/dashboard` and `/admin/audit-logs` do not exist (Tasya); `all_documents_approved()` and `REQUIRED_DOCUMENT_TYPES` are missing and any document type text is accepted (Dikshith); documents have no foreign keys to users and applications (Dikshith); the profile page has no exam-details form (Varun).

**Therefore not marked passed:** TC-009 (eligibility with real inputs), TC-011 (administrator seat management through the login), TC-020 (dashboard), TC-025 (audit log).

---

# Sprint 2 evidence: Gagan (1 November 2026)

Run on `main` at `932fd7e` (after #72 and #73) plus branch `feature/7-allotment-timing`. Same laptop: Windows 11, Intel64 Family 6 Model 197, Python 3.12.10. Fictional data only; every database was temporary and deleted afterwards.

## Test files behind my test cases

| Test case | Command (`python -m pytest -q ...`) | Observed |
|---|---|---|
| TC-004, TC-005 (draft, submit, exam details required, D2-02) | `tests/application` | 82 passed |
| TC-015, TC-016 (Appendix B oracle, rank order, own category only) | `tests/allotment/test_engine.py` | 44 passed |
| TC-015, TC-016, TC-028 (run on the database, refusals, rollback, two runs at once, write lock) | `tests/allotment/test_run_service.py` | 17 passed |
| TC-015, TC-022, TC-025 (API and console, 401/403, audit entry) | `tests/allotment/test_console_routes.py` | 9 passed |
| TC-028 (consistency script) | `tests/allotment/test_consistency_script.py` | 2 passed |
| TC-024 (HTTPS) | `tests/test_https.py` | 10 passed |
| TC-027 (timing script) | `tests/scripts/test_time_allotment.py` | 2 passed |
| Shared contracts | `tests/test_contracts.py` | 40 passed |

**The oracle tests can fail:** with the sort in `app/allotment/engine.py` changed to descending rank, `test_engine.py` and `test_run_service.py` gave 20 failed, 41 passed. The file was restored (`git diff` empty) and the tests passed again.

## TC-015 / TC-016: Appendix B oracle (issues #5, #6)

`test_appendix_b_oracle_results`, `test_appendix_b_oracle_seats_after_the_run` and `test_oracle_through_the_database` give exactly the expected values from the Test Plan:
C1 A-CSE (choice 1), C2 A-CSE (choice 1), C3 A-ISE (choice 2), C4 and C5 Not Allocated; seats left A-CSE 0, A-ISE 0, B-ECE 1. The run summary is 5 processed, 3 allocated, 2 not allocated. The expected values were not edited.

## TC-027 / ADM-NFR-002: allotment time (issue #7)

**Command:** `python scripts/time_allotment.py --candidates 300`, then `--candidates 600`. The script seeds a temporary database exactly like `flask seed-db`, adds Tasya's generator data (`scripts/make_demo_dataset.py`, seed 1), and times `run_allotment` three times, each on a fresh copy of that database.

| Dataset | Taking part (eligible + locked) | Allocated / Not Allocated | Run 1 | Run 2 | Run 3 | min / median / max | Seats after each run |
|---|---|---|---|---|---|---|---|
| 300 candidates | 210 | 143 / 67 | 0.921 s | 1.024 s | 0.967 s | 0.921 / 0.967 / 1.024 s | consistent |
| 600 candidates | 420 | 210 / 210 | 1.589 s | 1.711 s | 1.581 s | 1.581 / 1.589 / 1.711 s | consistent |

Both are far under the 1 minute limit. 600 candidates needed no code or architecture change. The three runs on each dataset gave the same outcome, as expected for a deterministic algorithm. The time includes loading candidates, re-checking eligibility, writing results, updating seats and the audit entry, all in one transaction.

## TC-028 / ADM-NFR-003 and TC-011 step 4: seat consistency (issue #8), 300 candidate dataset

One temporary database built as above, then driven through the real routes with the seeded administrator login and CSRF tokens (as a browser sends them):

| Step | Observed |
|---|---|
| `scripts/check_seat_consistency.py <file>` before the run | exit 0, "No allotment run yet ...", "consistent" |
| `POST /api/v1/admin/allotment/run` with no CSRF token | 400 `csrf_failed`, nothing run |
| Administrator login, `GET /admin/allotment` | 200, pre-run checks shown |
| First `POST /api/v1/admin/allotment/run` | 200: 210 processed, 143 allocated, 67 not allocated, run id 1, 810 ms |
| Second run | 409 "Allotment has already been run. There is one cycle only." |
| Console after the run | consistency tile "Passed", "0 mismatches", run button shows "already completed" |
| Audit log (`/admin/audit-logs.json`) | contains `allotment.run` |
| Catalogue `/colleges` | all 6 branches show "available / total" equal to the database; 143 of 240 seats filled; every seat row has available = capacity - filled |
| Check script after the run | exit 0, "consistent" |
| Seat row 1 changed by hand from filled 2 to 3 | check script exit 1: "MISMATCH seat row 1 (branch 1, General): filled 3, allotment records 2, capacity 30" |
| Direct `UPDATE ... SET filled = capacity + 1` | refused by the database: `CHECK constraint failed: ck_catalogue_seat_filled_within_capacity` |

Rollback (A-07) is covered by `test_a_failure_halfway_leaves_nothing_behind_and_is_audited_as_failed`: no run, no results, every `filled` back to 0, one audit entry with outcome "Failed", and a later run succeeds.

## TC-004 / TC-005 with the Sprint 2 rule (G3, D2-02)

`tests/application/test_exam_details_required.py`: submitting without exam details returns 422 on the page and the API with "Enter your exam details first", and the application stays a Draft; saving a draft without exam details still works. The Sprint 1 flow (draft saved and resumed, unique `ADM-YYYY-NNNNNN`, second submit 409) still passes in the same 82 tests.

## TC-024: HTTPS

`tests/test_https.py`: 10 passed on Sprint 2 `main` (no change since the Sprint 1 evidence above).

**Not done / limits:** times are from one laptop, not a server; the generator uses KCET ranks only, so mixed KCET/COMEDK ordering is covered by `test_comedk_and_kcet_ranks_are_compared_as_stored`, not by the timing data; no browser screenshots are included in this file.
