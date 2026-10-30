# Evidence: Tasya (Sprint 1)

## 1. Scope

This document records the test evidence for the Sprint 1 work completed by Tasya in the SE-Team5-Admission-Automation project.

The evidence covers the eligibility, catalogue, admin dashboard, and audit-related test runs. Results from separate feature branches are identified separately from tests run in the documentation branch.

## 2. Test Environment

- **Repository:** `SE-Team5-Admission-Automation`
- **Operating environment:** Kali Linux
- **Test framework:** pytest
- **Application:** Flask
- **Evidence branch:** `docs/tasya-sprint1-evidence`

Exact Python version, machine specifications, and test database configuration were not recorded in the supplied test outputs.

## 3. Test Execution Evidence

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

**Evidence:** The complete pytest suite available on the eligibility feature branch passed. The output confirms 38 passing tests; it does not independently identify the individual eligibility scenarios covered.

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

**Command 3 — Admin catalogue tests:**

```bash
python -m pytest -q tests/catalogue/test_admin.py
```

**Result:**

```text
20 passed in 1.22s
```

**Evidence:** The recorded catalogue test runs completed successfully. The admin-specific test run reported 20 passing tests. The earlier admin test run used a temporary `CATALOGUE_ADMIN_GUARD` configuration, so that configuration should be considered when interpreting the result.

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

**Evidence:** All five tests in the admin dashboard test file passed in the documentation branch's clean repository state.

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

**Evidence:** Both recorded audit test runs completed successfully. The individual test file reported eight passing tests, while the complete audit test directory reported fifteen.

## 4. Test Results Summary

| Area | Command / Scope | Result |
|---|---|---:|
| Eligibility | Complete suite on `feature/eligibility` | 38 passed |
| Catalogue | `tests/catalogue/` | 63 passed |
| Catalogue | Broader pytest run | 73 passed |
| Catalogue admin | `tests/catalogue/test_admin.py` | 20 passed |
| Admin dashboard | `tests/admin/test_dashboard.py` | 5 passed |
| Audit log | `tests/audit/test_audit_log.py` | 8 passed |
| Audit | `tests/audit/` | 15 passed |

These are results from separate test runs. They should not be added together as a unique total because some tests may overlap.

## 5. Limitations and Integration Notes

- Eligibility and catalogue results were obtained on their respective feature branches. They are historical test evidence, not a claim that those exact runs were repeated on the current branch.
- The catalogue admin test run used a temporary `CATALOGUE_ADMIN_GUARD` configuration.
- Dashboard and audit test results were obtained in the clean documentation-branch repository state.
- Test counts alone do not establish that every individual acceptance criterion or manual scenario passed.
- Further integration testing should be performed against the final merged application before claiming complete end-to-end acceptance.

## 6. Conclusion

The recorded Sprint 1 test executions show successful results across eligibility, catalogue, admin dashboard, and audit-related test areas.

The evidence distinguishes historical feature-branch results from the dashboard and audit tests executed in the documentation branch. Full integration and acceptance should be confirmed against the final merged application.
