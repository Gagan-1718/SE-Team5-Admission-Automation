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
