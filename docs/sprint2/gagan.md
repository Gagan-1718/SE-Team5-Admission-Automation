# Sprint Two brief: Gagan (allotment engine, release owner)

Read `SPRINT_TWO_START_HERE.md` first. This file is only your part.

## Your part of the final product

You build the one thing the whole project exists for: the administrator presses **Run allotment** once, and every eligible candidate with a locked choice list gets the best seat that their rank, their preference order and their category allow, with seat counts that are provably correct. You also own the administrator's allotment console, the application rule change, and the release: merging, regression, deviations, SAD update and the final tag.

What the user sees from your work: the allotment console at `/admin/allotment` (check, run, review, publish), and a seat in the candidate's result letter. Mockup: screen 7 in `docs/design/final-product-mockup.html`.

## Files you own this sprint

- New: `app/allotment/` (`models.py`, `engine.py`, `services.py`, `routes.py`; no `journey.py`, the candidate's result step belongs to the Result module), `templates/allotment/`, `tests/allotment/`, `scripts/time_allotment.py`, `scripts/check_seat_consistency.py`
- Day 1 only, shared: `app/__init__.py` (MODULES) and the six new models in the contracts PR
- Yours already: `app/application/` (rule change and restyle), `templates/application/`, `docs/DEVIATIONS.md`, `SAD_Python.md`
- Do not edit: `templates/base.html` and `static/css/app.css` (Varun), `app/security.py` (Dikshith), `app/audit/` (Tasya)

---

## Issue G0 (new): Shared contracts, schema and housekeeping

**Title:** `[SPRINT2] Merge shared tables, module skeletons and Sprint One leftovers`

**User story:** As a team member, I want the new tables and function names to exist on `main` before I start, so that four people can build in parallel and never wait on each other's schema.

**Requirement:** SPRINT_ONE_START_HERE rule: "A single coordinated schema change should be merged before dependent branches adopt it."

**Acceptance criteria**
- [ ] `MODULES` in `app/__init__.py` is `("accounts", "application", "documents", "catalogue", "eligibility", "choices", "allotment", "results", "audit", "admin")`.
- [ ] Models for `choices`, `choice_locks`, `allotment_runs`, `allotment_results`, `result_publications`, `seat_decisions` match section 4.2 of the start guide exactly, including the unique keys and the CHECK on `allotment_results`.
- [ ] Each new package has `services.py` with the agreed function names and signatures (raising `NotImplementedError` is fine), and every module in table 4.4 has a `journey.py` stub returning state `locked`.
- [ ] `flask --app app init-db --reset` and `seed-db` run clean; `tests/test_modules.py` and the full suite still pass.
- [ ] `docs/sprint1-final` is merged (or its pull request opened and reviewed), the 6 stale `xfail` marks in `tests/integration/test_demo_flow.py` are removed, and the README no longer tells people to check out `31-set-up-shared-spring-boot-app-and-mysql-connection` or says the profile has no exam form.
- [ ] `docs/DEVIATIONS.md` has D-16 (publication stored in `result_publications`) and D-17 (new modules use `/api/v1` paths as the SAD says).

**Tasks**
- [ ] Branch `chore/sprint2-contracts` from `main`. Add the three packages and models.
- [ ] Write one test per new table that creates a valid row and checks the key constraint (duplicate choice, second run with `cycle=1`, second publication for a run, second decision for a result, `Allocated` with no branch).
- [ ] Post in the group chat the moment it is merged: "pull main, run init-db --reset".

**Depends on:** nothing. **Blocks:** everyone's database work.
**Test reference:** none (enabling work). **Story points:** 2 | **Sprint:** 2
**Target:** merged within 90 minutes of the kickoff.

---

## Issue #5 `[ADM-F-015]` Implement rank/preference/category-based seat allotment

**User story:** As an administrator, I want to run seat allotment once, so that every eligible candidate with a locked list receives the best seat their rank, preferences and category allow, and seat counts stay correct.

**Requirement (from the board):** Automatically allot seats based on candidate rank, college preferences and category-wise seat availability.

**Acceptance criteria**
- [ ] `allot(candidates, seats)` in `app/allotment/engine.py` is a pure function: no database, no Flask, no clock.
- [ ] **Oracle (Test Plan Appendix B):** seats A-CSE 2, A-ISE 1, B-ECE 1, all General; C1 (rank 1) A-CSE, A-ISE; C2 (rank 2) A-CSE, B-ECE; C3 (rank 3) A-CSE, A-ISE; C4 (rank 4) A-CSE, A-ISE; C5 (rank 5) A-CSE. Result: C1 A-CSE, C2 A-CSE, C3 A-ISE, C4 Not Allocated, C5 Not Allocated; seats left A-CSE 0, A-ISE 0, B-ECE 1. This test runs in every CI run and is never edited to make it pass.
- [ ] Extended oracle (TC-015 step 3): category-specific seat rows (a General candidate never takes an OBC seat, per A-11) and one Not Eligible candidate whose locked list is ignored and who gets no result row.
- [ ] Candidates are processed in ascending rank; ties by reference number ascending (A-10); KCET and COMEDK ranks are compared as stored.
- [ ] Each candidate walks their locked choices in saved order and takes the first branch with a free seat in **their own category** row.
- [ ] `run_allotment(actor_id)` reads real data: `choices.services.locked_candidate_ids()` and `get_locked_branch_ids()`, `eligibility.services.get_eligibility()` (checked again at run time, D2-06), `catalogue` seat rows, rank and category from accounts, reference number from the submitted application.
- [ ] Seats are reduced immediately after each allocation (`catalogue_seat.filled`), inside one transaction.
- [ ] `POST /api/v1/admin/allotment/run` returns `{runId, allocatedCount, notAllocatedCount, durationMs}`. Anonymous 401, candidate 403, second run 409, nobody with a locked list 422 (D2-05).
- [ ] The run, the seat updates, the results, the completion row and the audit entry `allotment.run` commit together or not at all (SAD A-07).

**Tasks**
- [ ] Day 1: write the oracle tests first (they fail), then `allot()` until they pass. Add property-style checks: no seat count ever negative; each candidate appears once; output is deterministic when the input list is shuffled.
- [ ] Day 2: `run_allotment`. Take the write lock first, then check whether a completed run already exists, then load, allot, write, commit. With SQLite use the SQLAlchemy pysqlite recipe so the connection really issues `BEGIN IMMEDIATE`; prove it with a test where a second connection is refused while the first is open. Update seats with `UPDATE ... SET filled = filled + 1 WHERE id = ? AND filled < capacity` and treat `rowcount != 1` as a bug, so even a logic error cannot exceed capacity.
- [ ] Test: a deliberate failure halfway through leaves `filled`, results, runs and audit exactly as before (rollback).
- [ ] Test: two competing run requests; exactly one completes, the other gets 409 or a clear busy error and leaves nothing behind.
- [ ] Use `record_audit(..., commit=False)` from Tasya's Day 1 change. If it is not there yet, stub it and swap it in.
- [ ] Record a failed run in the audit log with outcome `Failed` after the rollback.

**Depends on:** ADM-F-009 and ADM-F-011 (done); ADM-F-012, 013, 014 (Varun, contract on Day 1, real on Day 2).
**Test reference:** TC-015 (also TC-022 for the 403, TC-025 for the audit entry). **Story points:** 8 | **Sprint:** 2

---

## Issue #6 `[ADM-F-016]` Record Not Allocated when no preference can be satisfied

**User story:** As a candidate whose choices were all full, I want my result to say Not Allocated, so that I know the outcome and am not left wondering.

**Requirement (from the board):** Candidates whose locked preferences cannot be satisfied are recorded as Not Allocated.

**Acceptance criteria**
- [ ] In the oracle, C4 and C5 get a result row with status `Not Allocated`, no branch, no seat, no choice priority.
- [ ] A candidate whose only choices are in a category with no seat row for them is Not Allocated, not an error.
- [ ] The database refuses an `Allocated` row without a branch and a `Not Allocated` row with a branch (the CHECK from G0).
- [ ] `allocated_count + not_allocated_count == candidates_processed` on every run.
- [ ] A candidate who was skipped (Not Eligible at run time, or never locked) has **no** row, so the result page can tell "Not Allocated" apart from "not part of this run" (D2-06).

**Tasks:** extend the oracle tests; add the count invariant to the run test; add one test for the skipped cases.
**Depends on:** #5. **Test reference:** TC-016. **Story points:** 3 | **Sprint:** 2

---

## Issue G2 (new): Administrator allotment console

**Title:** `[ADM-F-015] Admin page to check, run and review the allotment`

**User story:** As an administrator, I want one guarded page that walks me through check, run, review and publish in that order, so that I cannot run or publish by accident and I can see the result is consistent.

**Requirement:** SAD 4.5 "an allotment screen where Run and then Publish are enabled in that order"; ADM-F-015, ADM-F-017; SEC-F-002.

**Acceptance criteria**
- [ ] `/admin/allotment` is administrator only: anonymous redirected to login, candidate 403.
- [ ] Pre-run checks are shown with a pass or fail each: seat rows configured (count and total seats), number of Eligible candidates with locked lists, no completed run exists. Run is disabled with the reason when a check fails.
- [ ] Run asks for confirmation ("This can be done once and cannot be repeated") and then calls the same service as the API.
- [ ] After a run the page shows processed, allocated, not allocated, duration, the consistency check result (from #8) and seats filled by branch.
- [ ] Run is disabled for ever after a completed run; the page says so.
- [ ] The page includes Dikshith's `templates/results/_publish_card.html` and passes it the run; you do not implement publishing.
- [ ] Uses the shared shell and components (Varun). Matches screen 7 of the mockup.

**Tasks:** route and template; confirmation dialog (use Varun's `confirm` macro, or a plain `<dialog>` until it lands); test each state (before run, after run, published); screenshot for your evidence file.
**Depends on:** #5, #8, Varun's shell, Dikshith's partial (use a stub until it merges).
**Test reference:** TC-015, TC-022, TC-025. **Story points:** 3 | **Sprint:** 2

---

## Issue #7 `[ADM-NFR-002]` Validate allotment performance with seeded datasets

**User story:** As the project team, we want proof that allotment finishes quickly on a realistic dataset, so that the scalability requirement is met with evidence.

**Requirement (from the board):** Allotment completes within the agreed time for the demonstration dataset.

**Acceptance criteria**
- [ ] Using Tasya's generator, a run over about 300 candidates completes in under 1 minute; the measured time is recorded.
- [ ] A run over about 600 candidates also completes with no code or architecture change, and the time is recorded.
- [ ] `scripts/time_allotment.py` builds the dataset in a temporary database, runs allotment three times from a clean state, and prints min, median and max seconds.
- [ ] Results are written to `docs/evidence/gagan.md` with the date, machine, dataset size and command.

**Tasks:** wait for Tasya's generator (Day 1); write the script; run on Day 3 morning, or earlier on Day 2 if the run service is ready.
**Depends on:** #5, Tasya's dataset generator. **Test reference:** TC-027. **Story points:** 3 | **Sprint:** 2

---

## Issue #8 `[ADM-NFR-003]` Verify seat consistency and prevent over-allocation

**User story:** As an administrator, I want the system to prove after every run that no seat count exceeds capacity and every count matches the allotment records, so that I can trust the numbers I publish.

**Requirement (from the board):** After any allotment run, seat counts are consistent and capacity is never exceeded.

**Acceptance criteria**
- [ ] `seat_consistency_report()` returns an empty list when, for every college-branch-category row, `filled` equals the number of `Allocated` results pointing at that seat and `filled <= capacity`; otherwise it names each mismatch.
- [ ] `scripts/check_seat_consistency.py` runs the same check against any database file and exits non-zero on a mismatch.
- [ ] A test proves the database itself refuses `filled > capacity` (a direct `UPDATE` raises).
- [ ] After a run on the 300 candidate dataset the report is empty; the catalogue pages show available seats equal to capacity minus filled (TC-011 step 4).
- [ ] The console shows the check result after each run.
- [ ] Rollback test: a failed run leaves the report empty and all `filled` values unchanged.

**Tasks:** report function; script; tests including a deliberately corrupted row to prove the check can fail; wire into the console.
**Depends on:** #5, #6. **Test reference:** TC-028 (and TC-011 step 4). **Story points:** 5 | **Sprint:** 2

---

## Issue G3 (new): Application requires exam details; restyle and journey status

**Title:** `[ADM-F-005] Submit requires exam details; application page on the new design`

**User story:** As a candidate, I want the application page to tell me if my exam details are missing before I submit, so that I do not submit something the system cannot use for eligibility.

**Requirement:** ADM-F-004 depends on ADM-F-003; decision D2-02.

**Acceptance criteria**
- [ ] Submitting without exam details returns 422 (page and API) with the message "Enter your exam details first" and a link to the profile page; the application stays a Draft.
- [ ] Saving a draft without exam details still works.
- [ ] The draft page uses the shared components (page header, card, pill) and keeps every existing validation message.
- [ ] `app/application/journey.py` returns the `application` step: `current` while not started or Draft, `done` once Submitted with the reference number in `detail`.
- [ ] All existing application tests still pass; new tests cover the rule in page and API.

**Depends on:** Varun's shell (restyle part). **Test reference:** TC-004, TC-005. **Story points:** 2 | **Sprint:** 2

---

## Your release duties (not issues)

- Review pull requests promptly; Tasya is your reviewer and you are hers.
- Day 2 evening: run the whole suite on `main` and read the full-cycle test (Dikshith's) end to end.
- Day 3 afternoon: SAD revision 1.3 (real endpoint paths, new tables, deviations), final DEVIATIONS, defect triage, sprint review file, tag `v1.0`, close or merge every pull request, clear the board.

## Day checklist

**Day 1** [ ] G0 merged and announced  [ ] oracle tests written and passing on `allot()`  [ ] `run_allotment` skeleton with the lock and completion check
**Day 2** [ ] run service with rollback and two-run tests  [ ] console page  [ ] G3  [ ] audit entry `allotment.run` visible in the audit log
**Day 3** [ ] #7 and #8 evidence  [ ] TC-004, 005, 015, 016, 024, 027, 028 recorded  [ ] regression  [ ] SAD, DEVIATIONS, tag

## What you need from others and what you owe them

| You need | From | By |
|---|---|---|
| `record_audit(commit=False)` | Tasya | Day 1 |
| Choice service functions working | Varun | Day 1 evening |
| 300 candidate dataset script | Tasya | Day 1 evening |
| Publish card partial | Dikshith | Day 2 |

| You give | To | By |
|---|---|---|
| Contracts and schema PR | Everyone | Day 1, within 90 minutes |
| `get_result_for_candidate`, `get_completed_run` (working, not stubs) | Dikshith | Day 1 evening |
| `seat_consistency_report`, run summary (for the cycle banner) | Tasya | Day 2 |
| Console page with a slot for the publish card | Dikshith | Day 2 morning |

## Watch out

- The oracle file is the test plan's own data. If an oracle test fails, the engine is wrong, not the test.
- `catalogue_seat.filled` is shared with Tasya's catalogue pages. They already refuse to lower capacity below `filled`; do not change that.
- COMEDK rank 800 sorts before KCET rank 1000 in the seed data. That is the agreed behaviour (A-10); put it in the demo script so nobody is surprised.
- Do not call `get_eligibility` once per candidate in a way that loads all rules each time for 600 candidates; load the rules once per run and use the pure `evaluate_eligibility`.
