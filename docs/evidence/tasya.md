# Evidence: Tasya (Sprint 1)

## 1. Scope

This document records the Sprint 1 testing evidence for the work completed by Tasya in the SE-Team5-Admission-Automation project.

The evidence covers the following areas:

- Eligibility management
- College and branch catalogue
- Admin dashboard
- Audit logging
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

Exact Python version, machine specifications, and test database configuration were not recorded in the supplied test outputs.

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

## 4. Test Case Coverage and Status

The following test case IDs are referenced for the project evidence and traceability process.

| Test Case ID | Evidence Area | Recorded Status |
|---|---|---|
| TC-009 | Refer to the project's RTM/SRS for the exact scenario | Individual execution result not independently recorded |
| TC-010 | Refer to the project's RTM/SRS for the exact scenario | Individual execution result not independently recorded |
| TC-011 | Refer to the project's RTM/SRS for the exact scenario | Individual execution result not independently recorded |
| TC-020 | Refer to the project's RTM/SRS for the exact scenario | Individual execution result not independently recorded |
| TC-025 | Refer to the project's RTM/SRS for the exact scenario | Individual execution result not independently recorded |
| TC-026 | Refer to the project's RTM/SRS for the exact scenario | Individual execution result not independently recorded |
| TC-030 | Admin configuration and end-to-end integration scenario | Individual execution result not independently recorded |

**Important:** The automated pytest results in Section 3 demonstrate successful test executions for the listed test suites. They should not be treated as proof that every individual test case above passed.

The individual test case statuses must be updated after checking the corresponding test procedures and execution evidence on the integrated application.

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

These results are from separate test executions. They should not be added together as a unique test count because some tests may overlap.

## 6. Limitations and Integration Notes

- Eligibility results were recorded on the `feature/eligibility` branch.
- Catalogue results were recorded on the `feature/catalogue` branch.
- The catalogue admin test run used a temporary `CATALOGUE_ADMIN_GUARD` configuration.
- Dashboard and audit test results were recorded in the clean documentation-branch repository state.
- Test counts alone do not establish that every individual acceptance criterion or manual workflow passed.
- Individual test case execution records for TC-009, TC-010, TC-011, TC-020, TC-025, TC-026 and TC-030 must be verified against the project's RTM/SRS and integrated application.
- Full end-to-end acceptance should be confirmed against the final merged application.

## 7. Conclusion

The recorded Sprint 1 automated test executions show successful results across eligibility, catalogue, admin dashboard, and audit-related test areas.

This document preserves the actual recorded test outputs and distinguishes historical feature-branch results from tests executed in the documentation branch.

The listed test case references provide traceability for further verification. Final acceptance should only be claimed after the corresponding test scenarios have been executed and their results documented.
