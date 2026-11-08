# Part 3 Unit Test Report

Project: SE-Team5 Admission Automation
Report owner: Varun
Execution date for the independently rerun unit tests: 8 November 2026
Branch: `docs/varun-unit-test-report`
Commit under test: `d89e718bad7f58a4f826d343198fbac4b97a4e97`

## 1. Introduction

This report documents Varun's Part 3 unit-testing deliverable. It separates
isolated unit/component tests from Flask, SQLite, cross-module, security,
HTTPS and end-to-end executions. The full pytest suite is therefore not counted
as the unit-test total.

## 2. Testing objectives

The unit tests verify isolated business rules and helpers without relying on a
live application workflow or a production database. The selected scope covers
the eligibility decision function, the pure allotment algorithm, password
hashing helpers, and the Choices JavaScript controller's static component
contract. Integration and acceptance requirements remain documented as separate
executions.

## 3. Unit-test scope and classification

### Genuine unit/component tests

| Test module | Classification | Reason |
|---|---|---|
| `tests/eligibility/test_evaluate.py` | Unit | Calls `evaluate_eligibility` with in-memory rules and values; no Flask app or database. |
| `tests/allotment/test_engine.py` | Unit | Calls the pure `allot(candidates, seats)` algorithm with in-memory data, including the Appendix B oracle and generated values. |
| `tests/accounts/test_password_hashing.py` | Unit | Calls `hash_password` and `verify_password` directly; no account row, route or session. |
| `tests/choices/test_frontend_controller.py` | Component unit | Reads the owned JavaScript/template component and checks its API-operation, accessibility-feedback and failure-handling contract without a browser or server. |

These four modules contain 61 collected tests and are the only tests included
in the unit-test totals below.

### Other test classifications

| Test module/group | Classification | Reason |
|---|---|---|
| `tests/accounts/` except `test_password_hashing.py` | Integration / system | Uses Flask routes, temporary SQLite users, sessions, profile APIs and cross-module services. |
| `tests/application/` | Integration | Exercises real application models, database persistence and HTTP routes. |
| `tests/documents/` | Integration | Exercises document models, storage, migrations, database constraints and routes. |
| `tests/eligibility/` except `test_evaluate.py` | Integration | Uses Flask/SQLite services, seeded rules and journey/routes. |
| `tests/choices/` except `test_frontend_controller.py` | Integration | Uses database-backed choices, authorization, services and API/page routes. |
| `tests/allotment/` except `test_engine.py` | Integration | Uses database runs, transactions, audit records, seats and service/console routes. |
| `tests/results/` | Integration / system | Uses result models, publication, candidate routes and seat-decision persistence. |
| `tests/catalogue/`, `tests/admin/`, `tests/audit/` | Integration | Uses application fixtures, database entities and role-protected routes/services. |
| `tests/integration/` | System / end-to-end | Exercises multi-module admission journeys with real routes and fictional data. |
| `tests/security/`, `tests/test_security_headers.py` | Security/integration | Verifies CSRF, authentication, authorization and security headers through the application. |
| `tests/test_https.py` | Security/system | Starts real HTTPS/HTTP servers and checks TLS, cookies, redirects and network capture. |
| `tests/test_navigation.py`, `tests/test_ui_shell.py` | UI integration | Renders Flask templates and shared navigation/components. |
| `tests/test_contracts.py`, `tests/test_modules.py`, `tests/test_startup.py` | Contract/integration | Inspects application registration and agreed interfaces, with application fixtures and/or database state. |
| `tests/scripts/` | Script integration | Runs scripts with temporary databases/files and real service setup. |

## 4. Test environment

- Operating system: Windows PowerShell environment.
- Independently rerun unit-test interpreter: Python 3.11.9 (`py --version`).
- Independently rerun pytest: 9.1.1 (`py -m pytest --version`).
- Test data: fictional values and isolated test fixtures.
- Database: temporary SQLite databases supplied by `tests/conftest.py` where integration tests require them.
- Unit tests: no live database or Flask server required.
- Coverage artifact environment: Windows, Python 3.12.10, coverage.py 7.17.2, as recorded in the supplied coverage reports.

## 5. Unit-test execution

Exact independently executed command:

```powershell
py --version
py -m pytest -q tests/eligibility/test_evaluate.py tests/allotment/test_engine.py tests/accounts/test_password_hashing.py tests/choices/test_frontend_controller.py
```

Actual result on 8 November 2026:

```text
Python 3.11.9
61 passed in 1.31s
```

Collected: 61
Passed: 61
Failed: 0
Skipped: 0
Xfailed: 0
Xpassed: 0
Exit status: 0

## 6. Test results

The genuine unit-test result is **61 passed, 0 failed, 0 skipped**. This is not
the result of the complete project suite and does not include route, database,
security or HTTPS tests.

## 7. Failures and fixes

Only observed failures with available evidence are listed here.

| Failure | Observed failure | Root cause | Fix/evidence | Regression result |
|---|---|---|---|---|
| Allotment oracle investigation | A temporary descending-rank change caused `test_engine.py` and `test_run_service.py` to report 20 failed, 41 passed. | The experimental sort violated the agreed rank-order oracle. | The engine change was restored; the supplied evidence records the restored diff as empty. | `tests/allotment/test_engine.py`: 44 passed in the recorded regression evidence. |
| HTTPS registration fixture | HTTPS registration returned HTTP 400 after DOB became mandatory. | Shared registration fixture omitted `date_of_birth`. | Fixed in historical commit `b654751` (`test(accounts): update HTTPS registration fixture for DOB`). | Separate HTTPS execution: 10 passed. |
| CSRF registration fixture | CSRF registration fixture was incompatible with the mandatory DOB contract. | The fixture omitted the required DOB field. | Fixed in historical commit `976e99d` (`test(security): include required date of birth in CSRF registration`). | Included in the later recorded regression result; original failure log is not present in this checkout. |
| VARUN-001 / DEF-012 | Dashboard could display only `0 of 3` or `3 of 3`. | Dashboard used binary `all_documents_approved` logic. | Fixed by `get_document_summary(candidate_id)` and Dashboard integration; recorded in `docs/DEFECT_LOG.md`. | The fix was verified with 176 Documents tests, 20 Dashboard tests, 241 Accounts/Documents tests and a full run of 802 passed, 1 skipped, 6 xpassed. |

Where an original terminal log was not available, this report does not invent
the original node-level failure output; it identifies that limitation explicitly.

## 8. Coverage summary

The existing reports are:

- [Code Coverage Report](CODE_COVERAGE_REPORT.md)
- [Branch Coverage Report](BRANCH_COVERAGE_REPORT.md)
- [Coverage JSON](reports/coverage.json)
- [Coverage XML](reports/coverage.xml)

The reports state that coverage.py 7.17.2 measured Python files under `app/`
(67 files), using `--branch --source=app`. The reported results are:

- Statement coverage: **95.46%** — 2,545 of 2,666 executable statements.
- Branch coverage: **89.74%** — 542 of 604 branch destinations covered, with 52 partial locations.

These are application-code coverage measurements, not unit-test percentages,
requirements coverage, browser coverage or proof that every acceptance
criterion passed. The reports were supplied from Python 3.12.10 execution and
were not regenerated by this documentation task.

## 9. Overall Regression Execution — HTTPS Initially Skipped

This is a separate supplied execution and is not the unit-test total.

Exact command recorded in the coverage report:

```powershell
.\.venv\Scripts\python.exe -m coverage run --branch --source=app -m pytest -q
```

Observed result: **883 passed, 1 skipped in 499.26s**. The HTTPS module was
initially skipped because the optional `requirements-https.txt` dependencies
were not installed at that time. The raw terminal/JUnit log was not supplied;
the count is transcribed in the existing coverage reports.

## 10. HTTPS Verification — Separate Execution

This was run separately after the HTTPS dependencies were installed. The exact
installation command was not supplied; the repository identifies
`requirements-https.txt` as the dependency file.

Exact test command recorded in the coverage report:

```powershell
.\.venv\Scripts\python.exe -m coverage run --append --branch --source=app -m pytest tests/test_https.py -q -rs
```

Observed result: **10 passed in 27.96s**. This is not part of the original
883-test execution, and this report does not combine them into a single 893-test
run. The existing `docs/evidence/gagan.md` independently records the HTTPS
checks and their security observations.

## 11. Evidence references

- [Varun evidence](../evidence/varun.md)
- [Gagan HTTPS evidence](../evidence/gagan.md)
- [Dikshith evidence](../evidence/dikshith.md)
- [Updated TC-001–TC-030 test plan](TEST_PLAN_UPDATED.md)
- [Statement coverage](CODE_COVERAGE_REPORT.md)
- [Branch coverage](BRANCH_COVERAGE_REPORT.md)
- [Defect log](../DEFECT_LOG.md)
- [CI workflow](../../.github/workflows/ci.yml)

## 12. Limitations

- The independently rerun unit tests used Python 3.11.9 because the local Python launcher did not provide Python 3.12.
- The 3.12.10 full-regression and HTTPS counts are supplied historical execution evidence from the coverage reports, not newly rerun in this environment.
- Raw JUnit/terminal logs for the 883 and 10-test executions were not supplied.
- Unit tests do not establish route authorization, database integrity, browser accessibility, TLS behavior or complete SRS coverage.
- The repository's CI workflow installs Python 3.12 and HTTPS dependencies; CI status must be checked separately for this new documentation branch.

## 13. Conclusion

The genuine isolated unit/component scope contains 61 tests, all of which passed
in the independently executed Python 3.11.9 run. The broader 883-test regression
and the separate 10-test HTTPS verification are recorded as distinct supplied
executions. Coverage is reported from the existing Python 3.12.10 coverage
artifacts, with scope and limitations preserved.
