# ADM-F-008 verification and integration notes

## Implemented behavior

Candidates can view document status and replace an owned Rejected document.
The replacement uses the existing PDF/JPG/PNG content and 2 MiB validation.
Successful resubmission preserves document identity and type, resets status to
Pending, and clears the previous rejection reason. Pending and Approved documents
cannot be replaced. Requests require a session-bound form token.

The original file remains until the database commit succeeds. Database failure
rolls back metadata and removes the replacement. If deleting the old file fails
after a successful commit, the replacement remains valid and an error is logged;
the orphaned old file requires cleanup.

## Verification

- Automated service tests cover ownership, allowed status, invalid uploads,
  database failure recovery, and old-file cleanup failure.
- HTTP tests cover form tokens, ownership, missing files, request size, and the
  disabled identity fixture.
- The workflow test rejects a document, resubmits it as the candidate, verifies
  the administrator receives the replacement bytes, approves it, and confirms
  the candidate sees Approved and cannot resubmit again.
- On 2026-10-20, Dikshith reported that the local manual demo worked after checking
  the reject/resubmit flow. This was user-reported browser verification.

Run the suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Local Accounts/Application integration (2026-10-20)

Document routes now use real Accounts sessions and the shared administrator role
check. Upload and resubmission require the authenticated candidate's Submitted
application; browser-supplied candidate/application IDs are ignored. Resubmission
also checks the document's application link. The fixed-ID development identity
and configurable admin bypass have been removed.

Updated route tests use real logins. An additional whole-flow test registers a
candidate, submits an application, uploads a document, performs administrator
rejection, candidate resubmission and administrator approval, then verifies logout
revokes access. Final execution of the updated suite is pending: the agent's
terminal could not access the venv's installed Python runtime.

## Remaining team integration

Catalogue, eligibility, dashboard and audit contain placeholders in this checkout.
Their shared services are not yet available for document audit/eligibility events.
The documents table still uses integer links without database foreign keys;
route-level ownership/application checks are enforced, but an agreed migration
and existing-data validation remain necessary for database-level constraints.
No existing database or uploaded files were migrated or reset during this change.
Repeat browser acceptance checks with real candidate and administrator accounts.
