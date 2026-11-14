# System Validation Report — Sprint Two

**Project:** SE-Team5 Admission Automation  
**Prepared by:** Tasya  
**Status:** Part 3 documentation  
**Date:** 8 November 2026

## 1. Purpose

This report summarizes system-level validation of the Admission Automation application against the submitted SRS, SAD, and updated Test Plan. It records the validation scope, observed results, known limitations, and outstanding evidence considerations.

Validation was based on automated tests, integration checks, documented owner walkthroughs, and existing performance evidence. The report distinguishes demonstrated behavior from requirements that were only partially verified.

## 2. Test Environment

| Item | Environment |
|---|---|
| Application | Python 3.12, Flask, Flask-SQLAlchemy |
| Test framework | pytest and Flask test client |
| Database | Temporary SQLite database with foreign-key constraints |
| Test data | Fictional candidate and administrator records |
| HTTPS testing | Localhost with self-signed certificate and optional HTTPS dependencies |
| Browser testing | Automated HTTP/client checks; rendered HTML assertions do not constitute full browser testing |

The execution records supplied by the team include separate test runs and environments. Their results are reported independently rather than combined into a single execution count.

## 3. System Validation Results

| Test Case | Validation area | Result | Evidence / limitation |
|---|---|---|---|
| TC-001–TC-019 | Registration, application, eligibility, documents, candidate workflows | Passed — mapped automated scope | Corresponding automated checks were included in the R1 execution. Owner review of the mappings remains necessary. |
| TC-020 | Administrator candidate list, search, pagination and dashboard checks | Passed — D-23 scope | The dashboard, candidate-list search, pagination and access-control checks passed. Direct editing of candidate records remains outside the approved D-23 scope under DEF-013. |
| TC-021–TC-025 | Security, authorization, audit logging, allotment and publication workflows | Passed — mapped automated scope | Corresponding checks were included in R1. TC-025 has separate evidence for the allotment/result decision flow. |
| TC-026 | Candidate-page response time | Passed — 25-session local test | On 13 November 2026, 25 concurrent candidate journeys were simulated on the local Flask development server; 100/100 requests returned HTTP 200, with averages of 443.31 ms (login), 524.89 ms (dashboard), 387.35 ms (catalogue) and 331.28 ms (choices), all below 2 seconds. Local development-server limitations remain. |
| TC-027 | Allotment performance at scale | Passed — previously recorded benchmark | Gagan’s documented benchmark reports median times of 0.967 seconds for 300 candidates and 1.589 seconds for 600 candidates, against a 60-second limit. These are earlier benchmark results, not a new R1 measurement. |
| TC-028 | Allotment and seat consistency | Passed — mapped automated scope | Consistency checks were included in R1. Final owner review of the mapping remains necessary. |
| TC-029 | Usability / first-time-user walkthrough | **Limited evidence** | Owner walkthrough feedback was recorded. Participant-level completion counts, elapsed times, assistance counts, and a five-person usability record were not provided. |
| TC-030 | Admin configuration through candidate choices and allotment | Passed — demonstrated workflow | The integration test `tests/integration/test_demo_flow.py::test_admin_configured_catalogue_flows_through_choices_and_allotment` passed. Creation of a rule for a missing category is a separate acceptance detail not demonstrated by this workflow. |

**Interpretation:** “Passed — mapped automated scope” refers to automated checks associated with the case. It does not imply that every manual or broader acceptance criterion for the case was independently demonstrated.

## 4. Execution Summary

The team supplied the following distinct execution results:

| Execution | Result |
|---|---|
| R1 — main test execution | 883 passed, 1 skipped |
| R2 — HTTPS tests | 10 passed |
| R3 — coverage | 95.46% statement coverage; 89.74% branch coverage |

R1 and R2 are separate executions. Their counts should not be added and presented as one full-suite run. The skipped R1 test relates to optional HTTPS dependencies; the separate R2 execution was performed after those dependencies were installed.

The coverage figures are reported as supplied by the team and should be associated with their recorded coverage execution.

## 5. Defects and Deviations

The Sprint Two defect log records the following dispositions:

- DEF-001 through DEF-009 and DEF-011 through DEF-012 are documented as fixed.
- DEF-010 is documented as not a defect.
- DEF-013 is a scope decision under `docs/DEVIATIONS.md` D-23, not a defect. It preserves the historical decision that direct administrator editing of candidate records was intentionally excluded from approved scope.

D-23 concerns direct administrator editing of candidate records. The `/admin/candidates` page supports viewing, searching, pagination, dashboard checks and access control, while document correction is handled through the reject/resubmit workflow. Direct editing through `PUT /admin/candidates/{id}` was intentionally not implemented under the approved scope.

The deviation record states that no Critical or High defects remain open at the `v1.0` tag. This is reported as the team’s documented release status; it does not mean that every functional requirement is fully implemented.

## 6. Performance Validation

### TC-026 — Candidate response time

The recorded 13 November 2026 local concurrent measurement used 25 simultaneous candidate journeys and is the relevant evidence for this case.

| Page | Average response time |
|---|---:|
| Sign-in (`POST /accounts/login`) | 443.31 ms |
| Dashboard (`GET /dashboard`) | 524.89 ms |
| Catalogue (`GET /colleges`) | 387.35 ms |
| Choices (`GET /choices`) | 331.28 ms |

All 100 measured requests returned HTTP 200. The average response times were below the 2-second target, and the 25-session local load test was successful. The remaining limitation is that the test used the local Flask development server rather than a production deployment environment.

### TC-027 — Allotment performance

The previously documented benchmark results were:

| Candidate dataset | Median runtime |
|---|---:|
| 300 candidates | 0.967 s |
| 600 candidates | 1.589 s |

Both are below the documented 60-second allotment limit. These results are from Gagan’s earlier benchmark and are not claimed as a new benchmark from the R1 execution.

## 7. Validation Limitations

The following limitations should be considered when interpreting the results:

1. TC-020 covers the approved D-23 read-only administration scope: dashboard, search, pagination, record viewing and access control. Direct editing remains intentionally outside scope.
2. TC-026 was measured on the local Flask development server, not a production WSGI deployment; this is the remaining deployment limitation despite the successful 25-session local test.
3. TC-029 lacks participant-level usability measurements required to independently establish the full first-time-user protocol.
4. TC-030 demonstrates the configured catalogue → candidate choices → allotment workflow, but does not independently demonstrate creation of a rule for a missing category.
5. Automated Flask client checks and HTML assertions do not establish complete cross-browser validation.
6. Test-case mapping and owner review remain necessary before cases are marked Verified in the RTM.

## 8. Conclusion

The supplied automated execution results and integration evidence demonstrate substantial validation of the Admission Automation system’s candidate, administrator, security, audit, configuration, and allotment workflows.

The report preserves the known limitations rather than treating all acceptance criteria as fully verified. TC-020 passed for the approved D-23 read-only administration scope; TC-026 passed under the 25-session local development-server test; TC-029 has limited usability evidence; and TC-030's demonstrated catalogue-to-allotment workflow passed, but full ADM-NFR-005 verification remains partial because rule creation for a missing category is not independently evidenced.

The team’s deviation record states that no Critical or High defects remain open at the `v1.0` tag. The final RTM and Test Summary Report should retain the evidence-based distinctions documented here.
