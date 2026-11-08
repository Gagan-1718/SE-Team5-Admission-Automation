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
| TC-020 | Administrator candidate list and candidate record management | **Partial** | Candidate list/dashboard checks pass. Direct editing of candidate records is not implemented; this is the accepted gap DEF-013 / D-23. |
| TC-021–TC-025 | Security, authorization, audit logging, allotment and publication workflows | Passed — mapped automated scope | Corresponding checks were included in R1. TC-025 has separate evidence for the allotment/result decision flow. |
| TC-026 | Candidate-page response time | **Partial** | Historical single-client measurements were below the 2-second target. Concurrent-load validation is not demonstrated by those measurements. |
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
- DEF-013 is a Medium-severity known gap, deferred under `docs/DEVIATIONS.md` D-23.

D-23 concerns direct administrator editing of candidate records. The `/admin/candidates` page supports viewing, while document correction is handled through the reject/resubmit workflow. Direct editing through `PUT /admin/candidates/{id}` was not implemented.

The deviation record states that no Critical or High defects remain open at the `v1.0` tag. This is reported as the team’s documented release status; it does not mean that every functional requirement is fully implemented.

## 6. Performance Validation

### TC-026 — Candidate response time

The recorded historical single-client measurements were:

| Page | Average response time |
|---|---:|
| Login | 3.42 ms |
| Catalogue | 7.55 ms |
| Eligibility | 10.60 ms |
| Choices | 15.46 ms |

These results are below the 2-second target under the recorded conditions. However, they are historical measurements and do not demonstrate the concurrent 25-candidate condition described in the performance test plan. TC-026 is therefore reported as partial.

### TC-027 — Allotment performance

The previously documented benchmark results were:

| Candidate dataset | Median runtime |
|---|---:|
| 300 candidates | 0.967 s |
| 600 candidates | 1.589 s |

Both are below the documented 60-second allotment limit. These results are from Gagan’s earlier benchmark and are not claimed as a new benchmark from the R1 execution.

## 7. Validation Limitations

The following limitations should be considered when interpreting the results:

1. TC-020 does not include direct administrator editing of candidate records; the scope is deferred under D-23.
2. TC-026 does not demonstrate concurrent-load performance at 25 candidates.
3. TC-029 lacks participant-level usability measurements required to independently establish the full first-time-user protocol.
4. TC-030 demonstrates the configured catalogue → candidate choices → allotment workflow, but does not independently demonstrate creation of a rule for a missing category.
5. Automated Flask client checks and HTML assertions do not establish complete cross-browser validation.
6. Test-case mapping and owner review remain necessary before cases are marked Verified in the RTM.

## 8. Conclusion

The supplied automated execution results and integration evidence demonstrate substantial validation of the Admission Automation system’s candidate, administrator, security, audit, configuration, and allotment workflows.

The report preserves the known limitations rather than treating all acceptance criteria as fully verified. TC-020 and TC-026 remain partial, TC-029 has limited usability evidence, and TC-030 is passed for the demonstrated workflow with a separate rule-creation detail not yet evidenced.

The team’s deviation record states that no Critical or High defects remain open at the `v1.0` tag. The final RTM and Test Summary Report should retain the evidence-based distinctions documented here.
