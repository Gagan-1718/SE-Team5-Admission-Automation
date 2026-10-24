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

## Sprint One wrap-up (24 October 2026)

Main now provides catalogue, eligibility, dashboard and audit services. Document
reviews are audited and eligibility uses all_documents_approved(candidate_id).

The local wrap-up adds both document foreign keys and limits new uploads to the
three agreed types. Existing databases need the explicit upgrade-document-references
command documented in README.md. No personal database or upload was migrated or reset.

See docs/evidence/dikshith.md for current executed test evidence. Repeat browser
acceptance checks after applying the upgrade to a backed-up local database.
