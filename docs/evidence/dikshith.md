# Dikshith: Sprint One test evidence

Executed: 24 October 2026. Python 3.12.10 on Windows.
Working folder: New folder (7)/SE-Team5-Admission-Automation.
Local branch: fix/catalogue-admin-access (main merged locally; merge commit pending).

These are automated tests actually executed against temporary SQLite databases
and fictional files/accounts. No new browser run is claimed in this record.

## Acceptance cases

| Case | Checks actually executed | Command | Result |
|---|---|---|---|
| TC-006 | File signatures, extension/size limits, all three allowed types, forged/unknown type rejection, no partial file/metadata on failure. | Command A | PASS (53 tests) |
| TC-007 | Administrator approval/rejection, mandatory rejection reason, repeat-review protection, private downloads, audit entries and candidate denial. | Command A | PASS (50 tests) |
| TC-008 | Candidate status/reason visibility, owned Rejected-only replacement, Pending reset, failure cleanup and original-file preservation. | Command A | PASS (40 tests) |
| TC-022 | Every currently implemented admin route: administrator GET access, candidate 403, anonymous 401, denied requests leave data unchanged, logout revokes access. | Command A | PASS (32 tests) |

The groups overlap with other integration tests; their counts should not be added
to the full-suite totals.

## Executed commands and results

A. All tests except the socket-based HTTPS file (JUnit report used to verify the
acceptance-case results above):

```powershell
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_https.py --basetemp="C:\Users\Asus\Documents\Codex\2026-10-13\https-github-com-gagan-1718-se\work\sprint-wrap-final" --junitxml="C:\Users\Asus\Documents\Codex\2026-10-13\https-github-com-gagan-1718-se\work\sprint-wrap-final.xml" --tb=short
```

Result: PASS - 418 passed, 1 xfailed, 5 xpassed in 272.72s.

B. HTTPS tests, run separately with permission for temporary localhost connections:

```powershell
.\.venv\Scripts\python.exe -m pytest -v tests/test_https.py --basetemp="C:\Users\Asus\Documents\Codex\2026-10-13\https-github-com-gagan-1718-se\work\sprint-wrap-https" --junitxml="C:\Users\Asus\Documents\Codex\2026-10-13\https-github-com-gagan-1718-se\work\sprint-wrap-https.xml" --tb=short
```

Result: PASS - 10 passed in 18.48s.

Together A and B cover the entire collected suite: 428 passed, 1 xfailed,
5 xpassed, no failures or errors. This is the combined result of two commands,
not a claim that a single full-suite command produced that summary.

Earlier targeted document/audit/dashboard/eligibility/integration run:
220 passed, 1 xfailed, 5 xpassed.
Earlier merge-resolution catalogue/demo run:
70 passed, 3 xfailed, 6 xpassed before the document changes.

The remaining expected failure is the profile exam-details form owned by Varun.
The five XPASS cases are old expected-failure markers on working eligibility,
dashboard and audit integration checks. They are not counted as unimplemented
document work.

## Database integrity and upgrade

Command A also executed tests/documents/test_models.py and test_migrations.py:
both foreign keys exist; orphaned references and parent deletion are rejected;
failed uploads remove the new file; the SQLite upgrade preserves rows/ids/status/
rejection reasons, filenames and indexes; repeated upgrades are safe; orphaned
legacy rows stop the upgrade; a simulated rebuild failure rolls back without
losing the original table. All passed.

The upload service rejects types other than Marksheet, ID Proof and Category
Certificate. Old metadata is retained during migration rather than silently
rewritten. Route-level candidate/application ownership checks remain in place.

The upgrade was tested only on temporary databases. The developer's personal
database and uploads have not been changed. Back up the configured database and
uploads, stop Flask, then run upgrade-document-references as documented in README.

## Repository checks and delivery status

git diff --check and git diff --cached --check passed after conflict resolution.
No unresolved merge paths remain. Main's catalogue guard is retained alongside
the additional all-admin-route denial tests.

No commit, push, PR update or remote merge was performed by the coding agent.
The resolved main merge is staged separately from the unstaged document wrap-up.
SEC-F-002 coverage here applies to current Sprint One admin routes. Future
allotment/publication routes need the same checks when they are implemented.


## Follow-up: administrator HTML redirect (24 October 2026)

The HTML review queue and JSON list now have separate endpoint names.
The login page resolves documents.review_queue to /admin/documents; the JSON
URL remains available at /admin/documents.json. HTML review submissions redirect
back to the HTML queue. Authentication remains enforced on both endpoints.

Executed:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q tests/documents/test_review_routes.py tests/documents/test_integration_access.py tests/security/test_admin_authorization.py --basetemp="C:\Users\Asus\Documents\Codex\2026-10-13\https-github-com-gagan-1718-se\work\admin-html-redirect" --tb=short
~~~

Result: PASS - 35 passed in 21.87s. This targeted follow-up covers four new redirect/
response regression tests and the existing document and all-admin-route access checks.
The earlier broad-suite counts above describe the preceding run, before this follow-up.


## Sprint Two: publication service branch check (30 October 2026)

Branch: feature/12-publish-results-service. This is pre-merge service evidence,
not final TC-017 acceptance on main; routes, browser publication and result
visibility are still pending.

Executed on Python 3.12 against temporary SQLite databases:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q tests/results --basetemp="C:\Users\Asus\Documents\Codex\2026-10-13\https-github-com-gagan-1718-se\work\sprint2-publication" --tb=short
~~~

PASS: 13 passed in 6.61s (five existing model cases plus eight service cases).
Checks: publication metadata, single atomic results.publish audit entry,
unknown runs, candidate/missing-actor denial, duplicate publication, rollback
on audit/commit failure, and two independent sessions racing to publish with
exactly one winner and one audit entry. Shared schema and personal data unchanged.


### Publication API branch check (30 October 2026)

Added POST /api/v1/admin/allotment/runs/<run_id>/publish, guarded by the shared
administrator-role decorator. Actor identity comes from the authenticated session.
Returns 201 on success, 404 for unknown runs and 409 for duplicate publication.
Anonymous requests receive 401 and candidates 403 without publication or audit rows.
GET cannot publish, and logout revokes access.

Executed:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q tests/results tests/test_contracts.py tests/security/test_admin_authorization.py --basetemp="C:\Users\Asus\Documents\Codex\2026-10-13\https-github-com-gagan-1718-se\work\sprint2-publication-api" --tb=short
~~~

PASS: 63 passed in 23.63s. Includes seven new API cases.
This remains pre-merge evidence, not completed TC-017 acceptance.
Still pending: central CSRF integration, publish card, candidate result visibility,
full regression before PR review and a rerun on main after merge.
