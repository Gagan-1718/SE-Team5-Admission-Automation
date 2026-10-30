# Team 5 Sprint Two start guide

Sprint Two is the last sprint. It has **three working days: Day 1, Day 2 and Day 3**. The Test Plan (section 7) puts UAT at 30 October to 2 November and the Test Summary Report on 3 November, so if Day 1 is 30 October then Day 3 is 1 November. Confirm the real submission date at the first meeting and write it here: ____________.

Read this file first, then your own brief in `docs/sprint2/` (gagan.md, varun.md, tasya.md, dikshith.md). To see what the finished product looks like, open `docs/design/final-product-mockup.html` in a browser.

## What we are building in Sprint Two

Sprint One built the front half of the product: registration, login, profile and exam details, application, documents and their review, eligibility, the college catalogue, the audit log, the dashboard counts and HTTPS. Sprint Two builds the back half and makes the whole thing look and behave like one product: choice filling and locking, the allotment engine, result publication and the seat decision, plus a shared design, a candidate dashboard and the evidence the course asks for.

The Sprint Two demonstration is the whole cycle, with no gaps and no xfail: register (with date of birth) → log in → dashboard → profile and exam details → save and submit the application → upload three documents → administrator approves and rejects → candidate resubmits → eligibility becomes Eligible with a reason → candidate adds, reorders and locks choices → administrator runs allotment once and checks the seat counts → administrator publishes → candidate sees the result → candidate accepts or rejects once. The administrator also shows the dashboard, the candidate list, the editable eligibility rules and the audit log with every one of those actions in it.

## Where we start (checked on 30 October against `main` at 624d09c)

- 163 commits on `main`. The full suite gives **443 passed, 6 xpassed** and takes about 4 minutes. The 6 xpassed are old "not built yet" markers that now pass; they should be deleted.
- Merged and working: foundation, accounts, application, documents, catalogue, eligibility, audit log, admin dashboard counts, HTTPS, CI.
- Not merged: `docs/sprint1-final` (8 commits: demo script, `scripts/prepare_demo.py`, README and DEVIATIONS fixes) and PR #58 (Tasya's evidence).
- The README still tells people to check out the old branch `31-set-up-shared-spring-boot-app-and-mysql-connection`, and the TC table at the top of `docs/evidence/varun.md` still shows FAIL rows from before the merges (a corrected run is added below it, on Python 3.11.9 rather than 3.12, but the table itself was never updated).
- Open issues on the board (milestone Sprint 2): #5, #6, #7, #8 (Gagan); #21, #22, #23 (Varun); #28, #29, #30 (Tasya); #12, #13, #14, #15 (Dikshith).

### What is missing, and where the requirement comes from

| # | Gap | Source |
|---|---|---|
| 1 | No choice, allotment or result code at all | ADM-F-012 to ADM-F-019, TC-012 to TC-019 |
| 2 | No candidate dashboard; login sends candidates to the application page and administrators to the document queue | TC-002 says "redirected to dashboard"; SAD 4.5 step tracker |
| 3 | No date of birth at registration; no address on the profile | ADM-F-001 and TC-001; ADM-F-003; DEVIATIONS D-05 |
| 4 | CSRF protection only on the document forms | DEVIATIONS D-03; Test Plan addendum |
| 5 | Eligibility cut-offs cannot be edited in the admin UI | ADM-NFR-005, TC-030, issue #30 |
| 6 | Audit covers only catalogue edits and document review. Rule changes, candidate corrections, allotment run and publication are not logged | SEC-F-005, TC-025, issue #28 |
| 7 | Administrator cannot list or open a candidate record; the queue shows database ids, not names | ADM-F-020, SAD A-18 |
| 8 | `/colleges` can be opened without logging in | SEC-F-001; SAD access matrix |
| 9 | Exam details can still be changed after the application is submitted, and an application can be submitted without exam details | Integrity of rank and category (SAD A-09 intent) |
| 10 | Three unrelated page styles; home page still says "Feature modules are being added in Sprint One" | ADM-NFR-004 |
| 11 | No 300-candidate dataset, no response-time measurement, no usability session | TC-026, TC-027, TC-028, TC-029 |
| 12 | RTM still says "Planned" for every row; no Test Summary Report; evidence for TC-009 to TC-011, TC-020, TC-025 not on `main` | Test Plan sections 8 and 14 |

## Decisions to confirm in the first 30 minutes

The SRS is silent on these, and the product only makes sense if we all assume the same answer. The right-hand column is the recommendation; change it only if the whole team agrees, then write the final answer in the "Decided" column.

| ID | Question | Recommended answer | Built by | Decided |
|---|---|---|---|---|
| D2-01 | Can a candidate change exam details after submitting the application? | No. Editable until the application is Submitted, then read-only (409). Otherwise rank could change after documents are approved or choices locked. | Varun | |
| D2-02 | Can an application be submitted without exam details? | No (422 "Enter your exam details first"). Drafts can still be saved. | Gagan | |
| D2-03 | Choice rules | Only Eligible candidates can add. Lock needs at least one choice. A locked list can never be unlocked by anyone. No limit on list length. | Varun | |
| D2-04 | Can a candidate add a branch with 0 seats in their own category? | Yes, with a visible warning. An administrator may raise capacity later. | Varun | |
| D2-05 | May allotment run when nobody has a locked list? | No (422). The single cycle must not be spent on nothing. | Gagan | |
| D2-06 | Who is in the run? | Candidates who are Eligible **at run time** and have a locked list. Everyone else gets no result row, and their result page says "You were not part of this allotment run". That is different from Not Allocated. | Gagan, Dikshith | |
| D2-07 | Rank order across KCET and COMEDK, and ties | As stored, ties by application reference number (SAD A-10, unchanged). Note COMEDK 800 sorts before KCET 1000 in the seed data. | Gagan | |
| D2-08 | Where is "published" stored? | In its own table `result_publications` owned by the Result module, not as a status on the allotment run. Keeps one owner per module and makes "publish once" a database rule. Record as DEVIATIONS D-16. | Gagan, Dikshith | |
| D2-09 | Seat decision | One decision per allotted seat (database unique key). A rejected seat is not released (SAD A-12). | Dikshith | |
| D2-10 | Which pages are public? | Landing, sign-in and register only. The catalogue needs a login. | Tasya | |
| D2-11 | Where does login send you? | Candidate → `/dashboard`. Administrator → `/admin/dashboard`. | Varun | |
| D2-12 | What may an administrator correct on a candidate record (SAD A-18)? | Name and mobile only. Never rank, category or exam details. Every change is audited. | Tasya | |
| D2-13 | CSRF approach | One central check in `app/security.py` with a session-bound token, no new dependency (Flask-WTF is in the SAD but is not installed). Record as closing D-03. | Dikshith | |
| D2-14 | Status wording | The database keeps `Pending`; screens say "Pending Verification" through one shared helper (D-06). | Varun | |
| D2-15 | Schema change | After the Day 1 contracts PR everyone runs `flask --app app init-db --reset`, then `seed-db`, once. This deletes local data. | Everyone | |

## Shared contracts

This is what lets four people work at the same time. Gagan merges the tables (4.2) on Day 1 morning; the rest are agreed here and must not change without telling the group.

### 4.1 Names and statuses

| Item | Values |
|---|---|
| Existing | Application `Draft`/`Submitted`; Document `Pending`/`Approved`/`Rejected`; Eligibility `Pending`/`Eligible`/`Not Eligible`; categories `General`, `OBC`, `SC`, `ST`, `EWS`. Unchanged. |
| Choice list | open until a `choice_locks` row exists, then locked |
| Allotment result | `Allocated` / `Not Allocated` |
| Seat decision | none → `Accepted` / `Rejected` |
| Journey step state | `done`, `current`, `waiting`, `locked`, `problem` |

### 4.2 New tables (merged by Gagan, Day 1 morning)

```
choices (Varun)
  id, candidate_id FK users.id, branch_id FK catalogue_branch.id, priority INT, created_at
  UNIQUE (candidate_id, branch_id)             -- no duplicates, enforced by the database
  priorities are 1..n with no gaps; the service renumbers after remove and reorder

choice_locks (Varun)
  candidate_id PK FK users.id, locked_at

allotment_runs (Gagan)
  id, cycle INT NOT NULL DEFAULT 1 UNIQUE      -- the database itself allows one completed run (A-13)
  run_by FK users.id, started_at, completed_at, duration_ms,
  candidates_processed, allocated_count, not_allocated_count

allotment_results (Gagan)
  id, run_id FK, candidate_id FK users.id, UNIQUE (run_id, candidate_id),
  rank, category, reference_number,
  status 'Allocated' | 'Not Allocated',
  branch_id FK NULL, seat_id FK catalogue_seat NULL, choice_priority NULL,
  CHECK ((status = 'Allocated') = (branch_id IS NOT NULL))

result_publications (Dikshith)
  id, run_id FK allotment_runs UNIQUE, published_at, published_by FK users.id

seat_decisions (Dikshith)
  id, result_id FK allotment_results UNIQUE,   -- "exactly once" is a database rule
  decision 'Accepted' | 'Rejected', decided_at
```

`catalogue_seat.filled` (already exists, already `0 <= filled <= capacity`) is the only place seat usage is stored. Only the allotment run changes it.

### 4.3 Functions modules may call

```
choices.services (Varun)
  list_choices(candidate_id)                       -> [Choice] by priority
  add_choice(candidate_id, branch_id)              -> Choice     NotEligible 403 | DuplicateChoice 409 | ChoicesLocked 409 | UnknownBranch 404
  remove_choice(candidate_id, choice_id)           -> None       ChoicesLocked 409
  reorder(candidate_id, ordered_choice_ids)        -> [Choice]   ChoicesLocked 409 | OrderMismatch 400
  lock(candidate_id)                               -> None       AlreadyLocked 409 | NothingToLock 422
  is_locked(candidate_id)                          -> bool
  locked_candidate_ids()                           -> [int]      used by allotment
  get_locked_branch_ids(candidate_id)              -> [int]      priority order; [] if not locked

allotment.engine / allotment.services (Gagan)
  allot(candidates, seats)                         -> [result]   pure function, no database
        candidates: [{candidate_id, rank, reference, category, branch_ids:[...]}]   seats: {(branch_id, category): free}
  run_allotment(actor_id)                          -> RunSummary AlreadyCompleted 409 | NothingToAllot 422 | RunFailed 500
  get_completed_run()                              -> AllotmentRun | None
  get_result_for_candidate(candidate_id)           -> AllotmentResult | None
  seat_consistency_report()                        -> [Mismatch]  empty list means consistent

results.services (Dikshith)
  publish(run_id, actor_id)                        -> Publication  RunNotFound 404 | AlreadyPublished 409
  candidate_view(candidate_id)                     -> {state: NOT_PUBLISHED | NOT_IN_RUN | NOT_ALLOCATED | ALLOCATED, result?, decision?}
  decide(candidate_id, decision)                   -> SeatDecision NotPublished 404 | NotAllocated 422 | AlreadyDecided 409

audit.services (Tasya)
  record_audit(..., commit=True)                   -- new flag, Day 1. commit=False lets the allotment run
                                                      write its audit entry inside the same transaction (SAD A-07)
```

Existing functions we rely on: `accounts.services.get_exam_details`, `application.services.get_submitted_application`, `documents.services.all_documents_approved`, `eligibility.services.get_eligibility`, `catalogue.services.list_catalogue`.

### 4.4 The journey contract (feeds the candidate dashboard)

Each module that owns a step of the journey adds `app/<module>/journey.py` with `step_statuses(candidate_id) -> [step]`. The dashboard calls these and never reads another module's tables.

```
step = {"key": "documents", "label": "Documents", "state": "problem",
        "detail": "Marksheet and ID Proof approved. Category Certificate rejected.", "href": "/documents"}
```

| Module | Keys returned | Owner |
|---|---|---|
| accounts | `profile` | Varun |
| application | `application` | Gagan |
| documents | `documents` | Dikshith |
| eligibility | `eligibility` | Tasya |
| choices | `choices` | Varun |
| results | `result`, `decision` | Dikshith |

Meaning of the states: `done` finished; `current` the next thing the candidate should do; `waiting` waiting on someone else (administrator review, automatic eligibility); `locked` not available yet, `detail` says why; `problem` needs the candidate's attention (rejected document, Not Eligible, Not Allocated). The Day 1 contracts PR adds a stub returning `locked` in every module so the dashboard can be built before the real functions exist.

### 4.5 Routes

| Route | For | Owner |
|---|---|---|
| `GET /dashboard` | Candidate | Varun |
| `GET /choices`, `GET/POST /api/v1/choices`, `DELETE /api/v1/choices/<id>`, `PUT /api/v1/choices/order`, `POST /api/v1/choices/lock` | Candidate | Varun |
| `GET /admin/allotment`, `POST /api/v1/admin/allotment/run` | Admin | Gagan |
| `POST /api/v1/admin/allotment/runs/<runId>/publish` | Admin | Dikshith |
| `GET /result`, `GET /api/v1/allotment/result`, `POST /api/v1/allotment/decision` | Candidate | Dikshith |
| `GET /admin/candidates`, `GET /admin/candidates/<id>`, `PUT /admin/candidates/<id>` (HTML and JSON) | Admin | Tasya |
| `GET /admin/eligibility-rules` and its edit forms | Admin | Tasya |

Errors follow the SAD: JSON body `{status, error, message}`; 401 not logged in; 403 wrong role or not your record; 404 not found; 409 wrong state (locked, already run, already decided); 422 rule not met. Pages show the same message in the page, never a stack trace.

### 4.6 Audit action names

Dotted `noun.verb`, target type and id. Existing: `college.create`, `college.update`, `branch.create`, `branch.update`, `seats.update`, `document.approve`, `document.reject`. New: `rule.create`, `rule.update`, `candidate.update`, `allotment.run` (Gagan), `results.publish` (Dikshith). A failed allotment run is recorded with outcome `Failed`. Never put names, emails, mobile numbers or rejection reasons in an audit entry.

### 4.7 Who may edit shared files in Sprint Two

| File | Owner this sprint | Others |
|---|---|---|
| `templates/base.html`, `static/css/app.css`, `templates/_ui.html` | Varun | Ask Varun. Put page-specific CSS in your own `static/css/<module>.css`, using only the shared tokens. |
| `app/__init__.py` (MODULES) | Gagan, Day 1 only | Nobody else |
| `app/security.py` | Dikshith (CSRF) | Gagan reviews |
| `app/audit/services.py` | Tasya | Others only call it |

## Who does what

Story points are the same kind of estimate as on the board (#5 is 8, #2 was 3). They are proposals for planning, not a promise that the work fits.

| Person | Existing board issues | New issues to create | Points |
|---|---|---|---|
| Gagan | #5 allotment (8), #6 Not Allocated (3), #7 performance (3), #8 consistency (5) | Contracts and housekeeping (2); allotment console (3); application rules and restyle (2) | 26 |
| Varun | #21 add/remove/preview (5), #22 reorder (3), #23 lock (3) | Design system and app shell (5); candidate dashboard (5); date of birth, address, exam-details freeze (3) | 24 |
| Tasya | #28 audit (5), #29 response times (3), #30 rules admin UI (5) | Demo dataset generator (3); admin dashboard v2 and candidate records (5); eligibility, catalogue pages and `/colleges` login (3) | 24 |
| Dikshith | #12 publish (3), #13 result view (3), #14 decision (3), #15 usability (3) | CSRF everywhere (5); documents pages restyle (2); full-cycle integration test (3); final demo video and README (2) | 24 |

Do not close #28 or #30 until the acceptance criteria that depend on other people's modules have passed. Link pull requests with "Refs #n", not "Closes #n", for partial work.

## Day by day

Dates are relative on purpose. "Ready check" is the sentence that must be true before the next day starts.

| Day | Gagan | Varun | Tasya | Dikshith | Ready check |
|---|---|---|---|---|---|
| **1** | First 90 minutes: contracts and schema PR, merge `docs/sprint1-final`, delete xfail markers. Then the pure `allot()` function with the Appendix B oracle test. | Design system and shell merged **by end of Day 1**. Choices models in use; services and API with tests. | First 30 minutes: `record_audit(commit=False)`. Then the demo dataset generator and the rules admin page. | Result services against fake allotment rows. Central CSRF check and tests. Book five first-time users and write the usability script. | Everyone has run `init-db --reset`. Oracle test is green in CI. Shell is on `main`. Choice API passes its tests. Dataset script runs. |
| **2** | `run_allotment` on real data with transaction, rollback and two-run tests. Allotment console. Application rules and restyle. | Choices page with lock dialog. Candidate dashboard. Date of birth, address, exam freeze. Login redirects. Accounts pages on the new shell. | Admin dashboard v2, candidate list and record, audit expansion and screen, rules page finished, timing middleware, catalogue and eligibility pages restyled. | Publish card, `/result` and decision, CSRF in templates, documents pages restyled, full-cycle test, first usability sessions in the evening. | The whole cycle runs through the browser on seeded data. Nobody has work older than one day that is not on a pull request. |
| **3 morning** | Performance (#7) and consistency (#8) evidence on the 300 and 600 candidate datasets. Bug fixing. | Re-run account and choice cases, mobile and keyboard pass, bug fixing. | Response-time measurement (#29), TC-030 end-to-end, bug fixing. | Finish usability sessions, fix the top three difficulties. | **12:00 feature freeze.** After this only bug fixes. |
| **3 afternoon** | Full regression on `main`. DEVIATIONS and SAD updated. Tag. | Evidence files complete. | Test Summary Report and RTM. | Final demo video, README. | Everything in "Definition of done for the sprint" below. |

## The GitHub routine, with what we learned in Sprint One

The routine is unchanged: Todo → In Progress → update local `main` → feature branch → implement and test → commit and push → pull request → one peer review → fix → merge → Done only when every acceptance criterion passes. Suggested reviewers stay the same: Gagan and Tasya review each other; Varun and Dikshith review each other. Cross-module changes also need the affected teammate.

What went wrong in Sprint One and the rule that prevents it this time:

| Sprint One problem | Rule for Sprint Two |
|---|---|
| Chains of stacked pull requests, one with the wrong base branch, conflicting on `site.css` | Every pull request targets `main`. No stacking. Keep each one small, ideally under about 300 changed lines. |
| An admin guard that failed open | Guards deny by default. Every new route has a test for anonymous (401 or redirect), candidate (403) and the right role. |
| Issues closed before review or evidence | Mark Done only after the acceptance criteria pass and the evidence line is written in your `docs/evidence/` file. |
| Evidence recorded before the merges, showing failures that no longer exist | Evidence is recorded against `main` after merge, with the exact command and result. |
| Late integration | Merge `origin/main` into your branch at the start of each day and again before opening the pull request. |
| A 4-minute suite discourages running it | Run your own folder while working (`python -m pytest -q tests/<module>`). Run the full suite once before you ask for review. CI runs it on every push anyway. |

Merge order on Day 1: contracts and schema (Gagan) → audit flag (Tasya) → design system (Varun) → everything else as it is ready. On Day 2: choices → allotment run → results → dashboard and admin pages. Nobody merges to `main` after the Day 3 feature freeze unless it fixes a bug found in testing.

## Definition of done for the sprint

This is the software engineering evidence the Test Plan (sections 5, 8 and 14) and the SRS (section 8) ask for. The Test Plan exit criteria are: all TC-001 to TC-030 executed, no Critical or High defect open, every SRS acceptance criterion satisfied, 100% requirement coverage in the RTM, and the allotment oracle passing.

| Deliverable | Where | Who |
|---|---|---|
| Every TC executed on `main`, with command and result | `docs/evidence/<name>.md` | Each person, for the cases below |
| Test Summary Report: % executed and passed, defects by severity, requirement coverage 30 of 30, oracle and consistency result | `docs/TEST_SUMMARY_REPORT.md` | Tasya compiles; everyone sends evidence by Day 3 15:00 |
| Defect log with severity and disposition | `docs/DEFECT_LOG.md` | Everyone logs, Gagan triages |
| Updated RTM (Planned → Verified, with TC and evidence link) | `SRS_Draft.md` section 8, noted in `DOCUMENT_CHANGE_RECORD.md` | Tasya |
| SAD revision 1.3: real endpoint paths, new tables, deviations | `SAD_Python.md` | Gagan |
| Deviations closed or explained: D-03, D-05, D-16 and any new ones | `docs/DEVIATIONS.md` | Gagan |
| Final README, run steps, demo walkthrough | `README.md` | Dikshith |
| Demo script and video | `docs/demo/`, video file | Dikshith |
| Usability report (5 first-time users) | `docs/evidence/usability.md` | Dikshith |
| Sprint review and retrospective, three lines from each person | `docs/SPRINT2_REVIEW.md` | Gagan compiles |
| Release tag `v1.0`, all pull requests merged or closed, board cleared | GitHub | Gagan |

Test cases per person (all 30 are covered):

| Person | Cases |
|---|---|
| Gagan | TC-004, 005, 015, 016, 024, 027, 028 |
| Varun | TC-001, 002, 003, 012, 013, 014, 021, 022, 023 |
| Tasya | TC-009, 010, 011, 020, 025, 026, 030 |
| Dikshith | TC-006, 007, 008, 017, 018, 019, 029 |

Rules for evidence: only results that were actually run are recorded; a case that failed is recorded as failed, logged as a defect and re-run after the fix.

## Risks for three days

| Risk | What we do |
|---|---|
| The allotment is the heart of the project and SQLite serialises writers | Gagan builds and tests the pure function against the oracle first (no database), then the transaction. Two competing runs and a deliberate mid-run failure are tests, not manual checks. |
| The shell lands late and every page restyle slips | Varun merges the shell by end of Day 1 with the old stylesheets still loaded, so nothing breaks while owners migrate page by page on Day 2. |
| CSRF breaks hundreds of tests | The check is off when `TESTING` is on, and a dedicated test file turns it on. |
| Five first-time users are hard to find | Dikshith books them on Day 1. Friends, juniors and family who have never seen the app count; team members do not. |
| Someone is blocked | Say so in the group chat within two hours. The person who owns the dependency drops what they are doing or pairs. |
| Demo-day surprises | `scripts/prepare_demo.py` resets and seeds the demo. Rehearse once on Day 3 afternoon from a clean clone. |

## What to say to the team

"This is the last sprint, and it has three days. Sprint One gave us a working front half. Now Varun builds choices, the design everyone uses and the candidate dashboard. I build the allotment engine and its admin screen. Tasya makes the administrator side complete and measures it. Dikshith builds results, the seat decision, CSRF and the usability test. We agreed the tables and function names this morning, so everyone starts at once and nobody waits. Every pull request goes to main and is small. We stop adding features at noon on Day 3 and spend the afternoon proving it all works, with evidence, the way the test plan says."
