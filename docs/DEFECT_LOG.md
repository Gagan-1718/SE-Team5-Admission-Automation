# Defect log (Sprint Two)

Started 1 November 2026. Everyone logs; Gagan triages. A defect is anything where the product or a test did not do what the SRS, SAD, Test Plan or an agreed contract says. Only defects that were actually observed are logged, with how they were found.

**Severity** (Test Plan): Critical = data loss, security hole or the cycle cannot finish; High = a requirement is not met; Medium = a requirement is met only partly or in a wrong way; Low = cosmetic, test-only or documentation.
**Disposition:** Fixed (with pull request or commit), Open (with owner), Deferred (accepted as a known gap, written in `docs/DEVIATIONS.md`), Not a defect.

The exit criterion is: no Critical or High defect open at the `v1.0` tag.

| ID | Found | How found | Description | Requirement / TC | Severity | Disposition | Owner |
|---|---|---|---|---|---|---|---|
| DEF-001 | Sprint 1 | Review against the test plan addendum | No CSRF token on accounts, application, catalogue and eligibility forms (DEVIATIONS D-03) | SEC, TC-021 | High | Fixed in #73 (central session-bound token); verified on 1 Nov: a scripted POST without a token gets 400 | Dikshith |
| DEF-002 | Sprint 1 | Review against the SRS | Registration did not collect date of birth (D-05) | ADM-F-001, TC-001 | Medium | Fixed in #72 | Varun |
| DEF-003 | 31 Oct | `tests/security/test_admin_authorization.py` | Allotment console redirected anonymous visitors to the login page instead of 401 like every other admin route | TC-022 | Medium | Fixed before merge (`fc450c7`, #70) | Gagan |
| DEF-004 | 31 Oct | Full suite after the D2-02 submit rule | 20 tests in other modules failed because their fixtures submitted applications without exam details | D2-02, TC-005 | Low (test fixtures) | Fixed before merge: fixtures enter exam details first (#69) | Gagan |
| DEF-005 | Day 1 | Review of the choices pull request against the shared contract | Choice service return values and lock behaviour did not match the agreed contract | ADM-F-012 to ADM-F-014 | Medium | Fixed (`dac2be7`, #67) | Varun |
| DEF-006 | Day 2 | Found by the owners while connecting their pages | Choices and eligibility-rules links in the shared shell were disabled after the pages existed | ADM-NFR-004 | Low | Fixed (`979b05a` Varun, `6d713e4` Tasya) | Varun, Tasya |
| DEF-007 | 1 Nov | Full suite showed 6 `xpassed` | Six Sprint 1 `xfail` tests in `tests/integration/test_demo_flow.py` had started passing, so a later break would have been hidden | TC-009, 020, 025 | Low (test-only) | Fixed: marks removed, 12 passed (`feature/7-allotment-timing`) | Gagan |
| DEF-008 | 1 Nov | Review of `main` routes | Candidate result page and seat decision are not built: no `/result`, `GET /api/v1/allotment/result` or decision endpoint (DEVIATIONS O-01) | ADM-F-018, ADM-F-019, TC-017 to TC-019 | High | Open: must be merged before the tag | Dikshith |
| DEF-009 | 1 Nov | Review of `main` routes | Administrator candidate list is not built (`/admin/candidates`) (O-02) | ADM-F-020, TC-020 | Medium | Open | Tasya |
| DEF-010 | 1 Nov | Test output | `TLSV1_ALERT_UNKNOWN_CA` message printed during `tests/test_https.py` | TC-024 | n/a | Not a defect: it is the server noting the test client that correctly refuses the self-signed certificate | Gagan |

## How to add a defect

Add a row with the next ID, the date, how you found it (test name, manual step, review), what happened, the requirement or TC, a proposed severity and "Open" with your name. Gagan sets the final severity. When it is fixed, write the pull request number and how the fix was checked.
