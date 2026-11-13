# TC-026 — Candidate Page Response-Time Verification

**Owner:** Tasya  
**Requirement:** ADM-NFR-001  
**Target:** Average response time ≤ 2 seconds  
**Environment:** Local Flask development server, Python 3.12.15, Flask 3.1.3, Werkzeug 3.1.9  
**Test dates:** 1 November 2026 (sequential test); 13 November 2026 (concurrent test)

## 1. Test method

### 1.1 Sequential test

- Used the local application at `http://127.0.0.1:5000`.
- Performed one warm-up request followed by 10 measured requests per page.
- Public pages were measured using Python HTTP requests.
- Authenticated candidate pages were measured in the logged-in browser using Fetch with same-origin credentials.
- Recorded HTTP status and elapsed response time.
- No concurrent-user load was applied.

### 1.2 Concurrent test

- Used the isolated local test database `instance/load_test.db`, separate from the normal application database.
- Generated a demo dataset containing 300 fictional candidates.
- Used the local Flask development server at `http://127.0.0.1:5001` with threaded request handling.
- Simulated 25 concurrent candidate journeys using separate candidate sessions.
- Each candidate fetched the login page, obtained a session-specific CSRF token, signed in, and accessed the dashboard, college catalogue and choices page.
- Measured the HTTP response time for each endpoint.
- Recorded successful HTTP responses, average response time, 95th percentile (P95), and maximum response time.
- No application source code or existing templates were modified for the test.

## 2. Sequential test results

| Page | Requests | Successful responses | Average | Maximum |
|---|---:|---:|---:|---:|
| `/accounts/login` | 10 | 10 (HTTP 200) | 3.42 ms | 3.70 ms |
| `/colleges` | 10 | 10 (HTTP 200) | 7.55 ms | 10.20 ms |
| `/eligibility` | 10 | 10 (HTTP 200) | 10.60 ms | 13.60 ms |
| `/choices` | 10 | 10 (HTTP 200) | 15.46 ms | 18.60 ms |

All four tested pages returned HTTP 200 for all measured requests. All observed average response times were below the 2-second target.

The candidate account used for testing was ineligible for choice filling because its rank was 90,000, above the General category cut-off.

## 3. Concurrent test results

**Dataset:** 300 fictional candidates  
**Concurrent candidates:** 25  
**Requests:** 25 per endpoint  
**Total measured requests:** 100

| Page | Requests measured | HTTP 200 | Other statuses | Average | P95 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| Sign-in (`POST /accounts/login`) | 25 | 25 | 0 | 443.31 ms | 831.18 ms | 925.23 ms |
| Dashboard (`GET /dashboard`) | 25 | 25 | 0 | 524.89 ms | 725.94 ms | 787.60 ms |
| Catalogue (`GET /colleges`) | 25 | 25 | 0 | 387.35 ms | 558.97 ms | 560.27 ms |
| Choices (`GET /choices`) | 25 | 25 | 0 | 331.28 ms | 418.12 ms | 444.83 ms |

All 100 measured requests returned HTTP 200. No failed HTTP responses were recorded.

All measured average and P95 response times were below the 2-second target.

## 4. Evaluation

The sequential test demonstrated that the selected candidate-facing pages responded successfully under single-client conditions.

The concurrent test further demonstrated that the sign-in, dashboard, catalogue and choices endpoints handled 25 simultaneous candidate journeys against a 300-candidate demo dataset.

The average response times for all tested endpoints were below the 2-second requirement. The P95 response times in the concurrent test were also below 2 seconds.

The sequential and concurrent measurements were collected under different test conditions and should be interpreted separately.

## 5. Conclusion

**TC-026 passed for the tested pages under the recorded local test conditions.**

The sequential test verified the selected pages under single-client conditions. The concurrent test successfully completed 25 candidate journeys, with all 100 measured endpoint requests returning HTTP 200 and all average response times remaining below the ADM-NFR-001 target.

**Limitations:**

- Tests were conducted using the local Flask development server, not a production WSGI deployment.
- The concurrent test used a locally generated fictional dataset and does not establish production-scale capacity.
- Results may vary with hardware, database configuration, network conditions and deployment environment.
- The concurrent test covered sign-in, dashboard, catalogue and choices; it did not include the eligibility page.

These results provide local verification evidence for ADM-NFR-001 but are not a production performance guarantee.
