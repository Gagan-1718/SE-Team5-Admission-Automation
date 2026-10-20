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

## Remaining integration

Candidate identity currently uses the explicitly enabled localhost/debug fixture.
Replace it with authenticated Accounts identity and Application access/submission
checks. Replace the administrator guard callback with shared role authorization.
Connect required audit events to the shared audit service and verify the flow
again with real accounts and application records before closing issue #10.

This branch builds on feature/9-documents-review. Review the PR against that branch
while its changes remain unmerged; reassess the base after the dependency merges.
