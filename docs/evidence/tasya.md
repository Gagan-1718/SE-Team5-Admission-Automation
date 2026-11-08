
# Evidence: Tasya (Sprint 1 and Sprint 2)

## 1. Scope

This document records the testing evidence for the work completed by Tasya in the SE-Team5-Admission-Automation project.

The evidence covers:

- Eligibility management
- College and branch catalogue
- Admin dashboard
- Audit logging
- Candidate response-time verification
- Audit logging and result decision flow
- Related application test execution

It includes automated pytest results, test case references, branch information, and integration limitations.

## 2. Test Environment

| Item | Details |
|---|---|
| Repository | `SE-Team5-Admission-Automation` |
| Operating System | Kali Linux |
| Application | Flask |
| Testing Framework | pytest |
| Evidence Branch | `docs/tasya-sprint1-evidence` |
| Test Database | Project test database configuration |

Exact Python version, machine specifications, and test database configuration were not recorded in the supplied Sprint 1 test outputs.

## 3. Automated Test Execution Evidence

### 3.1 Eligibility Tests

**Branch:** `feature/eligibility`

**Command:**

```bash
python -m pytest -q
```

**Result:**

```text
38 passed in 0.70s
```

**Observation:**

The complete pytest suite available on the eligibility feature branch completed successfully, with 38 passing tests.

The output confirms the overall test result but does not independently identify the individual test scenarios covered.

### 3.2 Catalogue Tests

**Branch:** `feature/catalogue`

**Command 1:**

```bash
python -m pytest -q tests/catalogue/
```

**Result:**

```text
63 passed in 2.89s
```

**Command 2:**

```bash
python -m pytest
```

**Result:**

```text
73 passed in 3.92s
```

**Command 3 — Admin Catalogue Tests:**

```bash
python -m pytest -q tests/catalogue/test_admin.py
```

**Result:**

```text
20 passed in 1.22s
```

**Observation:**

The catalogue test directory reported 63 passing tests. The broader pytest run reported 73 passing tests, and the admin catalogue test file reported 20 passing tests.

The admin catalogue test run used a temporary `CATALOGUE_ADMIN_GUARD` configuration. This should be considered when interpreting the result.

### 3.3 Admin Dashboard Tests

**Branch:** `docs/tasya-sprint1-evidence`

**Command:**

```bash
python -m pytest -v tests/admin/test_dashboard.py
```

**Result:**

```text
5 passed in 2.47s
```

**Observation:**

All five tests in the admin dashboard test file passed in the documentation branch's clean repository state.

### 3.4 Audit Log Tests

**Branch:** `docs/tasya-sprint1-evidence`

**Individual audit test file:**

```bash
python -m pytest -v tests/audit/test_audit_log.py
```

**Result:**

```text
8 passed in 3.12s
```

**Complete audit test directory:**

```bash
python -m pytest -v tests/audit/
```

**Result:**

```text
15 passed in 7.30s
```

**Observation:**

The individual audit test file reported eight passing tests. The complete audit test directory reported fifteen passing tests.

Both recorded executions completed successfully.

## 4. Sprint 2 Test Case Evidence

### 4.1 TC-025 — Audit Logging and Result Decision Flow

**Requirement:** SEC-F-005 — Audit logging of privileged actions
**Status:** Passed

**Command:**

```bash
pytest tests/allotment/test_result_decision_flow.py -v
```

**Result:**

```text
1 passed in 1.60s
```

**Observation:**

The end-to-end test verified seat configuration, allotment execution, result publication, candidate result access, and candidate decisions. It also checked the expected audit actions.

The test provides evidence for the integrated audit and result decision flow.

### 4.2 TC-026 — Candidate Response-Time Verification

**Requirement:** ADM-NFR-001 — Response time performance
**Status:** Partial — the tested pages met the 2-second target under single-client conditions; concurrent-load verification remains pending.

The candidate-facing login, college catalogue, eligibility, and choices pages were measured.

The recorded average response times were:

| Candidate Page | Average Response Time |
|---|---:|
| Login | 3.42 ms |
| College Catalogue | 7.55 ms |
| Eligibility | 10.60 ms |
| Choices | 15.46 ms |

All measured page averages were below the two-second response-time target.

**Test conditions and limitations:**

- One warm-up request followed by ten measured requests per page.
- Sequential single-client testing.
- Public pages were tested using Python HTTP requests.
- Authenticated pages were tested using same-origin Fetch requests in a logged-in browser.
- This was not a concurrent load test.

Detailed measurements and test conditions are recorded in:

`docs/evidence/tasya-response-time.md`
### 4.3 TC-030 — Admin Catalogue, Seat, and Eligibility Configuration

**Requirement:** ADM-NFR-005 — Configurable, data-driven maintainability

**Status:** Passed

The integration test verifies that an administrator can create a college and branch, configure seat capacity, and update the General eligibility cutoff. It confirms that the candidate becomes eligible after the cutoff is updated, sees the configured college and branch in the candidate-facing catalogue, submits and locks a choice, and receives the configured seat through the allotment process.

**Command:**
```bash
pytest tests/integration/test_demo_flow.py -v
```

**Result:** 12 passed in 6.90s.

**Evidence:** The test `test_admin_configured_catalogue_flows_through_choices_and_allotment` passed. It verifies the complete flow from administrator configuration through candidate eligibility, catalogue visibility, choice submission, and successful allotment. It also confirms that the configured seat capacity is one, the filled seat count is one, and the candidate's allotment result is `Allocated`.

This records the automated TC-030 integration scenario. Additional manual UAT evidence, if required, should be recorded separately.



## 5. Test Results Summary

| Test Area | Test Command / Scope | Result |
|---|---|---:|
| Eligibility | Complete suite on `feature/eligibility` | 38 passed |
| Catalogue | `tests/catalogue/` | 63 passed |
| Catalogue | Broader pytest run | 73 passed |
| Catalogue Admin | `tests/catalogue/test_admin.py` | 20 passed |
| Admin Dashboard | `tests/admin/test_dashboard.py` | 5 passed |
| Audit Log | `tests/audit/test_audit_log.py` | 8 passed |
| Audit | `tests/audit/` | 15 passed |
| TC-025 | `tests/allotment/test_result_decision_flow.py` | 1 passed |
| TC-026 | Candidate-facing response-time measurements | Partial — single-client measurements met the target; concurrent load test pending |
| **TC-030** | `tests/integration/test_demo_flow.py` — admin-configured catalogue flow | 12 passed |

These results are from separate test executions. They should not be added together as a unique test count because some tests may overlap.

## 6. Limitations and Integration Notes

- Eligibility results were recorded on the `feature/eligibility` branch.
- Catalogue results were recorded on the `feature/catalogue` branch.
- The catalogue admin test run used a temporary `CATALOGUE_ADMIN_GUARD` configuration.
- Dashboard and audit test results were recorded in the clean documentation-branch repository state.
- Test counts alone do not establish that every individual acceptance criterion or manual workflow passed.
- TC-025 has a recorded individual test execution.
- TC-026 has documented response-time measurements and test conditions.
- **TC-030** has a recorded passing integration test for the admin-configured catalogue, choices, and allotment flow.
- Full end-to-end acceptance should be confirmed against the final merged application.

## 7. Conclusion

The recorded automated test executions show successful results across eligibility, catalogue, admin dashboard, audit-related test areas, and the Sprint 2 TC-025 audit and result decision flow.

TC-026 met the documented two-second average response-time target under the recorded single-client test conditions. However, the required concurrent-user workload has not yet been tested; therefore, the overall performance requirement remains partially verified.

**TC-030** passed the recorded admin-configured catalogue integration scenario. The result is documented above.
