# Code Coverage Report - Part 3

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

## Statement coverage result

| Measurement | Actual result |
|---|---:|
| Executable statements | 2666 |
| Covered statements | 2545 |
| Missing statements | 121 |
| Excluded statements | 0 |
| **Statement coverage** | **95.46%** |

Calculation: **2545 / 2666 x 100 = 95.46%**. This is a weighted application total, not an average of file percentages. When branch measurement is enabled, coverage.py's terminal Cover column is a combined line-and-branch metric; it must not be labelled as statement coverage. This export's combined value is 94.40%.

## Per-file statement coverage

| File | Statements | Covered | Missing | Statement coverage |
|---|---:|---:|---:|---:|
| `app/__init__.py` | 38 | 38 | 0 | 100.00% |
| `app/accounts/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/accounts/auth.py` | 69 | 66 | 3 | 95.65% |
| `app/accounts/constants.py` | 2 | 2 | 0 | 100.00% |
| `app/accounts/journey.py` | 8 | 7 | 1 | 87.50% |
| `app/accounts/models.py` | 39 | 39 | 0 | 100.00% |
| `app/accounts/routes.py` | 202 | 188 | 14 | 93.07% |
| `app/accounts/security.py` | 12 | 8 | 4 | 66.67% |
| `app/accounts/seed.py` | 39 | 34 | 5 | 87.18% |
| `app/accounts/services.py` | 8 | 8 | 0 | 100.00% |
| `app/admin/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/admin/routes.py` | 31 | 31 | 0 | 100.00% |
| `app/admin/services.py` | 59 | 58 | 1 | 98.31% |
| `app/allotment/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/allotment/engine.py` | 25 | 25 | 0 | 100.00% |
| `app/allotment/models.py` | 36 | 36 | 0 | 100.00% |
| `app/allotment/routes.py` | 55 | 55 | 0 | 100.00% |
| `app/allotment/services.py` | 106 | 101 | 5 | 95.28% |
| `app/application/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/application/identity.py` | 28 | 28 | 0 | 100.00% |
| `app/application/journey.py` | 15 | 15 | 0 | 100.00% |
| `app/application/models.py` | 29 | 29 | 0 | 100.00% |
| `app/application/routes.py` | 115 | 114 | 1 | 99.13% |
| `app/application/services.py` | 106 | 103 | 3 | 97.17% |
| `app/audit/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/audit/models.py` | 24 | 24 | 0 | 100.00% |
| `app/audit/routes.py` | 19 | 19 | 0 | 100.00% |
| `app/audit/services.py` | 19 | 18 | 1 | 94.74% |
| `app/catalogue/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/catalogue/access.py` | 2 | 2 | 0 | 100.00% |
| `app/catalogue/models.py` | 114 | 107 | 7 | 93.86% |
| `app/catalogue/routes.py` | 102 | 102 | 0 | 100.00% |
| `app/catalogue/seed.py` | 15 | 15 | 0 | 100.00% |
| `app/catalogue/services.py` | 105 | 102 | 3 | 97.14% |
| `app/choices/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/choices/journey.py` | 14 | 14 | 0 | 100.00% |
| `app/choices/models.py` | 18 | 18 | 0 | 100.00% |
| `app/choices/routes.py` | 88 | 75 | 13 | 85.23% |
| `app/choices/services.py` | 116 | 108 | 8 | 93.10% |
| `app/cli.py` | 25 | 23 | 2 | 92.00% |
| `app/documents/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/documents/access.py` | 2 | 2 | 0 | 100.00% |
| `app/documents/journey.py` | 27 | 27 | 0 | 100.00% |
| `app/documents/migrations.py` | 61 | 54 | 7 | 88.52% |
| `app/documents/models.py` | 11 | 11 | 0 | 100.00% |
| `app/documents/routes.py` | 164 | 162 | 2 | 98.78% |
| `app/documents/services.py` | 99 | 96 | 3 | 96.97% |
| `app/documents/storage.py` | 31 | 30 | 1 | 96.77% |
| `app/documents/validation.py` | 57 | 53 | 4 | 92.98% |
| `app/eligibility/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/eligibility/evaluation.py` | 12 | 12 | 0 | 100.00% |
| `app/eligibility/journey.py` | 20 | 20 | 0 | 100.00% |
| `app/eligibility/models.py` | 13 | 12 | 1 | 92.31% |
| `app/eligibility/routes.py` | 83 | 54 | 29 | 65.06% |
| `app/eligibility/seed.py` | 10 | 10 | 0 | 100.00% |
| `app/eligibility/services.py` | 16 | 16 | 0 | 100.00% |
| `app/extensions.py` | 11 | 11 | 0 | 100.00% |
| `app/journey.py` | 17 | 16 | 1 | 94.12% |
| `app/main.py` | 26 | 26 | 0 | 100.00% |
| `app/results/__init__.py` | 0 | 0 | 0 | N/A (no statements) |
| `app/results/journey.py` | 18 | 18 | 0 | 100.00% |
| `app/results/models.py` | 23 | 23 | 0 | 100.00% |
| `app/results/routes.py` | 68 | 68 | 0 | 100.00% |
| `app/results/services.py` | 118 | 116 | 2 | 98.31% |
| `app/security.py` | 35 | 35 | 0 | 100.00% |
| `app/setup_check.py` | 13 | 13 | 0 | 100.00% |
| `app/tls.py` | 48 | 48 | 0 | 100.00% |

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

## Reproduce the export

After the measured runs, regenerate the artifacts from the repository root:

```powershell
.\.venv\Scripts\python.exe -m coverage html -d docs/testing/reports/coverage-html
.\.venv\Scripts\python.exe -m coverage xml -o docs/testing/reports/coverage.xml
.\.venv\Scripts\python.exe -m coverage json -o docs/testing/reports/coverage.json
```

Conclusion: statement coverage is **95.46%**, with **121 executable statements unexercised** in this measurement. The missing source lines remain visible in the supporting JSON/HTML; they have not been excluded to improve the result.
