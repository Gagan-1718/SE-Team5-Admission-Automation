# Branch Coverage Report - Part 3

Project: SE-Team5 Admission Automation  
Report date: 8 November 2026  
Environment: Windows, Python 3.12.10, coverage.py 7.17.2  
Coverage export timestamp: `2026-11-08T16:08:13.940940` (local timestamp from coverage.json)  
Local HEAD inspected when preparing these reports: `d3eb5cdc1d18bc0fd4b51b27803529b4ce35f15a`.

The measured executions were performed by Dikshith in folder (11). Results below are calculated from the existing machine-generated coverage.json; pytest counts and durations are taken from his supplied terminal output. The execution-time commit and working-tree state were not independently captured, so the inspected HEAD above is a reference, not proof of an immutable test baseline.

## Executions that produced the data

1. Full-suite command:

```powershell
.\.venv\Scripts\python.exe -m coverage run --branch --source=app -m pytest -q
```

Observed terminal result: **883 passed, 1 skipped in 499.26s**. The skipped HTTPS module required the optional requirements-https.txt dependencies.

2. After installing those dependencies, append the HTTPS tests:

```powershell
.\.venv\Scripts\python.exe -m coverage run --append --branch --source=app -m pytest tests/test_https.py -q -rs
```

Observed terminal result: **10 passed in 27.96s**. Coverage from these two commands is merged. This is not a claim that a single complete rerun produced 893 passed with zero skips. The initial skip remains in its historical execution record; the previously skipped HTTPS tests subsequently passed. The server's UNKNOWN_CA message corresponds to the deliberate untrusted-certificate check, not a pytest failure.

## Branch coverage result

| Measurement | Actual result |
|---|---:|
| Measured branch destinations | 604 |
| Covered branch destinations | 542 |
| Missing branch destinations | 62 |
| Partially covered branch locations | 52 |
| **Branch coverage** | **89.74%** |

Calculation: **542 / 604 x 100 = 89.74%**. A partial location and a missing destination are different counts: one source location can have multiple outgoing destinations. The partial count therefore need not equal the missing count.

Instrumentation used **--branch --source=app**, with **--append** for the HTTPS follow-up. This measures Python control-flow branches/arcs. It is not MC/DC or exhaustive Boolean-condition coverage, a measure of user journeys, or a count of Git branches. Files with no measured branches are N/A, not evidence that a branching path was tested.

## Per-file branch coverage

| File | Branch destinations | Covered | Missing | Partial locations | Branch coverage |
|---|---:|---:|---:|---:|---:|
| `app/__init__.py` | 10 | 8 | 2 | 2 | 80.00% |
| `app/accounts/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/accounts/auth.py` | 20 | 17 | 3 | 3 | 85.00% |
| `app/accounts/constants.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/accounts/journey.py` | 2 | 1 | 1 | 1 | 50.00% |
| `app/accounts/models.py` | 2 | 1 | 1 | 1 | 50.00% |
| `app/accounts/routes.py` | 52 | 45 | 7 | 7 | 86.54% |
| `app/accounts/security.py` | 4 | 2 | 2 | 2 | 50.00% |
| `app/accounts/seed.py` | 18 | 15 | 3 | 1 | 83.33% |
| `app/accounts/services.py` | 2 | 2 | 0 | 0 | 100.00% |
| `app/admin/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/admin/routes.py` | 2 | 2 | 0 | 0 | 100.00% |
| `app/admin/services.py` | 8 | 7 | 1 | 1 | 87.50% |
| `app/allotment/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/allotment/engine.py` | 14 | 14 | 0 | 0 | 100.00% |
| `app/allotment/models.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/allotment/routes.py` | 2 | 2 | 0 | 0 | 100.00% |
| `app/allotment/services.py` | 20 | 17 | 3 | 3 | 85.00% |
| `app/application/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/application/identity.py` | 8 | 8 | 0 | 0 | 100.00% |
| `app/application/journey.py` | 8 | 8 | 0 | 0 | 100.00% |
| `app/application/models.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/application/routes.py` | 16 | 15 | 1 | 1 | 93.75% |
| `app/application/services.py` | 44 | 43 | 1 | 1 | 97.73% |
| `app/audit/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/audit/models.py` | 2 | 1 | 1 | 1 | 50.00% |
| `app/audit/routes.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/audit/services.py` | 6 | 5 | 1 | 1 | 83.33% |
| `app/catalogue/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/catalogue/access.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/catalogue/models.py` | 28 | 25 | 3 | 3 | 89.29% |
| `app/catalogue/routes.py` | 10 | 10 | 0 | 0 | 100.00% |
| `app/catalogue/seed.py` | 8 | 8 | 0 | 0 | 100.00% |
| `app/catalogue/services.py` | 32 | 32 | 0 | 0 | 100.00% |
| `app/choices/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/choices/journey.py` | 4 | 4 | 0 | 0 | 100.00% |
| `app/choices/models.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/choices/routes.py` | 12 | 8 | 4 | 2 | 66.67% |
| `app/choices/services.py` | 28 | 26 | 2 | 0 | 92.86% |
| `app/cli.py` | 6 | 5 | 1 | 1 | 83.33% |
| `app/documents/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/documents/access.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/documents/journey.py` | 10 | 10 | 0 | 0 | 100.00% |
| `app/documents/migrations.py` | 24 | 17 | 7 | 7 | 70.83% |
| `app/documents/models.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/documents/routes.py` | 38 | 37 | 1 | 1 | 97.37% |
| `app/documents/services.py` | 32 | 30 | 2 | 2 | 93.75% |
| `app/documents/storage.py` | 6 | 4 | 2 | 2 | 66.67% |
| `app/documents/validation.py` | 22 | 19 | 3 | 3 | 86.36% |
| `app/eligibility/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/eligibility/evaluation.py` | 6 | 6 | 0 | 0 | 100.00% |
| `app/eligibility/journey.py` | 8 | 8 | 0 | 0 | 100.00% |
| `app/eligibility/models.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/eligibility/routes.py` | 12 | 5 | 7 | 3 | 41.67% |
| `app/eligibility/seed.py` | 4 | 4 | 0 | 0 | 100.00% |
| `app/eligibility/services.py` | 4 | 4 | 0 | 0 | 100.00% |
| `app/extensions.py` | 2 | 1 | 1 | 1 | 50.00% |
| `app/journey.py` | 4 | 4 | 0 | 0 | 100.00% |
| `app/main.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/results/__init__.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/results/journey.py` | 10 | 10 | 0 | 0 | 100.00% |
| `app/results/models.py` | 0 | 0 | 0 | 0 | N/A (no branches) |
| `app/results/routes.py` | 4 | 4 | 0 | 0 | 100.00% |
| `app/results/services.py` | 32 | 30 | 2 | 2 | 93.75% |
| `app/security.py` | 12 | 12 | 0 | 0 | 100.00% |
| `app/setup_check.py` | 2 | 2 | 0 | 0 | 100.00% |
| `app/tls.py` | 4 | 4 | 0 | 0 | 100.00% |

## Supporting artifacts

- [Machine-readable coverage JSON](reports/coverage.json): source of the totals, per-file measurements and missing paths.
- [Coverage XML](reports/coverage.xml): machine-readable report for tooling.
- [Interactive HTML report](reports/coverage-html/index.html): annotated source and missing branches. Open locally after downloading if GitHub displays the HTML source.

Raw pytest/JUnit execution logs were not supplied with this coverage export; the pass counts above are transcribed from the owner's terminal results, not from a newly generated JUnit report.

## Limits and interpretation

- Scope is Python files under **app/**, including unexecuted files discovered by coverage.py. There are 67 files in this export.
- tests/, scripts/, config.py, templates, HTML, CSS and JavaScript are outside this stated Python application metric. The result does not establish browser rendering or JavaScript coverage.
- Subprocess Python execution is not automatically covered unless separately instrumented.
- Coverage is execution evidence, not proof of correct assertions, complete requirement acceptance, human usability or security completeness.
- No minimum coverage percentage is specified in the Part 3 brief; this report records measurements without inventing a threshold or granting release sign-off.
- Regenerate both reports if application code or tests change. Do not reuse these percentages as measurements of a later build.

## Review of unexecuted paths

Use each file's missing_branches list in coverage.json or the highlighted HTML source to identify the actual source-to-destination arcs. Review missed authorization, validation, rollback and failure-handling paths according to their risk; do not assume that every missing path is cosmetic or unreachable.

Conclusion: branch coverage is **89.74%**, with **62 branch destinations unexercised** across **52 partial locations**. These are retained in the report rather than hidden by exclusions. The separate statement coverage result is documented in [Code Coverage Report](CODE_COVERAGE_REPORT.md).
