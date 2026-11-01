# TC-026 — Candidate Page Response-Time Verification

**Owner:** Tasya
**Requirement:** ADM-NFR-001
**Target:** Average response time <= 2 seconds
**Environment:** Local Flask development server, Python 3.12.15, Flask 3.1.3, Werkzeug 3.1.9
**Test date:** 1 November 2026

## Test method

- Used the local application at `http://127.0.0.1:5000`.
- Performed one warm-up request followed by 10 measured requests per page.
- Public pages were measured using Python HTTP requests.
- Authenticated candidate pages were measured in the logged-in browser using Fetch with same-origin credentials.
- Recorded HTTP status and elapsed response time.
- No concurrent-user load was applied.

## Results

| Page | Requests | Successful responses | Average | Maximum |
|---|---:|---:|---:|---:|
| /accounts/login | 10 | 10 (HTTP 200) | 3.42 ms | 3.70 ms |
| /colleges | 10 | 10 (HTTP 200) | 7.55 ms | 10.20 ms |
| /eligibility | 10 | 10 (HTTP 200) | 10.60 ms | 13.60 ms |
| /choices | 10 | 10 (HTTP 200) | 15.46 ms | 18.60 ms |

## Evaluation

All four tested pages returned HTTP 200 for all measured requests.
All observed average response times were below the 2-second target.

The candidate account used for testing was ineligible for choice filling because its rank was 90,000, above the General cutoff of 20,000. The choices page nevertheless loaded successfully and displayed the eligibility restriction.

## Conclusion

TC-026 passed for the tested pages under the local, sequential test conditions.

**Limitation:** This was a lightweight single-client test, not a concurrent-user or production-load test. Results should not be interpreted as proof of performance under normal or peak load.
