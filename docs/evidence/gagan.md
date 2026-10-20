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
