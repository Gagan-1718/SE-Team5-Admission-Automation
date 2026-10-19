# Team 5 Sprint One start guide

Meeting date: 19 October 2026. Sprint One: 19–23 October. Sprint Two: 26–30 October.

## What we are building

One Python Flask website with candidate and administrator pages. SQLite stores records in a local database file. Candidates apply; administrators manage colleges and verify documents; software checks eligibility and later allocates seats. Use fictional data. Keep the existing SRS requirements and test identifiers.

The Sprint One demonstration is: register → log in → profile with seeded exam details → save and reopen draft → submit with reference number → upload document → administrator approves/rejects → candidate sees status and can resubmit → eligibility updates. Also demonstrate a small editable college catalogue, basic admin counts, audit records for implemented actions, and HTTPS in the acceptance environment. Choice locking, allotment and published results belong in Sprint Two.

## First meeting in order

1. Agree Python, Flask, SQLite and simple HTML pages. Everyone uses the same dependency versions and one repository. No separate React application.
2. Gagan owns shared setup; Tasya helps with schema and seed data. Varun owns accounts/profile. Dikshith owns admin access and documents.
3. Agree shared names before coding: user ID, candidate ID, application ID, document ID; Draft/Submitted; Pending Verification/Approved/Rejected; Eligible/Not Eligible/Pending Verification. Use the SAD API contract and existing requirement IDs.
4. Choose fictional exam records, two colleges, a few branches, category seat counts and sample eligibility rules. Agree required documents and maximum file size; 2 MB is a proposal to align with the test plan, not a verified product limit.
5. Review the schedule below against each person's availability. These are proposed daily targets, not proof of board dates or guaranteed completion. If setup slips, replan together immediately.
6. Each person picks one issue, assigns it, and moves it to In Progress only when actually starting. Do not move the whole sprint there.

## Who starts what and when

| Date | Gagan | Varun | Tasya | Dikshith | Ready check |
|---|---|---|---|---|---|
| 19 Oct | Create shared Flask skeleton, dependency file, home page, setup README and setup PR | Agree user/profile data; start registration, password hashing and login on the shared skeleton | Agree schema with Varun; prepare seed script and sample colleges/seats | Agree admin role checks with Varun; prepare document validation cases and upload design | All four run the same starter and create/read a database record using the README |
| 20 Oct | Draft application save/resume using agreed candidate ID; begin HTTPS environment setup | Finish login/logout and seeded exam profile; protect candidate routes | Admin college/branch/seat entry and candidate catalogue | Enforce admin permissions; implement upload against agreed application ID | Candidate login/profile and draft are integrated; candidate is denied admin access |
| 21 Oct | Final submission, required-field validation and unique reference; integrate with documents | Help integrate profile/application; test duplicate accounts, ownership and logout | Finish catalogue; implement basic admin counts and audit writing/reading | Upload, admin approve/reject with reason, status and resubmission | A submitted application can pass through document review |
| 22 Oct | Fix integrated application flow; complete HTTPS verification | Test authentication and other-candidate access; help fix integration | Eligibility using exam rules and document status; integrate audit for implemented actions | Finish review/resubmission; test invalid uploads and unauthorized document access | End-to-end Sprint One flow works with both approval and rejection |
| 23 Oct | Run demo and coordinate fixes/review | Run identity/profile acceptance cases | Run catalogue/eligibility/admin/audit cases | Run document and permissions cases | Peer-reviewed PRs merged, actual test evidence recorded, only accepted whole issues marked Done |

Start work in parallel after agreeing interfaces. A dependency means the final integrated feature needs its prerequisite; it does not mean everyone must wait idle. Mock data is useful while coding but does not prove an integrated issue is Done.

## Sprint scope and issue mapping

The previously reviewed board had ten Sprint-One-only issues, two shared issues, and eight of Varun's issues without a sprint. This plan explicitly proposes adding five of those missing prerequisites to Sprint One.

| Person | Sprint One issues | Sprint Two |
|---|---|---|
| Gagan | Setup #31; drafts #2; submission #3; HTTPS #4 | Allotment #5; Not Allocated #6; performance #7; consistency #8 |
| Varun | Registration #16; login/logout #17; profile #18; authentication #19; password hashing #20 | Choices #21; reorder #22; lock #23 |
| Tasya | Eligibility #24; catalogue #25; dashboard #27; Sprint One portions of college/seat administration #26 and audit #28 | Complete #26 and #28 integration; response times #29; configuration acceptance #30 |
| Dikshith | Upload #1; review #9; resubmit #10; admin permissions #11 | Publish #12; results #13; decision #14; usability #15 |

This means 15 feature/security issues targeted for full completion, plus setup, plus portions of two shared issues. It is more work than the earlier shorthand “12 issues”. Confirm capacity at the meeting; splitting an issue into smaller tracked tasks is preferable to pretending it is done. Do not close #26 or #28 if their Sprint Two acceptance work remains. No story points or promises of feasibility are inferred from the count.

## Shared foundation and handoff

Gagan creates one Flask package with separate module files/folders for accounts, applications, documents, catalogue, eligibility and admin. Tasya coordinates database changes. Use a repeatable schema/seed command: each developer gets a separate local SQLite file from the same schema and fictional seeds. Never exchange a live database file through Git. Keep uploaded files and secrets out of Git too.

Varun and Gagan agree the identity interface; Gagan and Dikshith agree application/document links; Tasya consumes exam and document status for eligibility. A single coordinated schema change should be merged before dependent branches adopt it. Use separate test databases. Keep SQLite foreign keys enabled and verify all business constraints.

## The GitHub routine

For each issue: Todo → In Progress → update local main → create a feature branch → implement and test → commit and push → open a PR → request one peer review → fix feedback → merge → mark Done only if all acceptance criteria pass. Keep a partially implemented issue In Progress. Link PRs to issues, but avoid automatic closing keywords for partial work.

Suggested reviewers: Gagan and Tasya review each other; Varun and Dikshith review each other. Cross-module changes also need the affected teammate's input. Gagan coordinates integration but does not write or approve every change himself. Everyone pulls merged changes regularly. Do not share account passwords.

## What to say to the team

“We are building one Python website together. Today our first win is that all four laptops run the same starter. Then Varun builds accounts, I build applications, Tasya builds colleges and eligibility, and Dikshith builds documents and admin checks. We work on separate branches and join our changes through reviewed pull requests. By Friday we aim to demonstrate application submission and verification. Seat allotment comes next sprint.”
