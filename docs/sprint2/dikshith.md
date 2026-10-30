# Sprint Two brief: Dikshith (results, seat decision, CSRF, usability and the final demo)

Read `SPRINT_TWO_START_HERE.md` first. This file is only your part.

## Your part of the final product

You build the end of the candidate's journey and the security and proof that go around it.

- The administrator **publishes** the allotment with one guarded click. Until then, no candidate can see anything.
- The candidate opens **their result**: a printable allotment letter if they got a seat, a clear explanation if they did not, and one chance to **accept or reject**.
- You make every state-changing request in the product **CSRF-safe** with one central check, closing deviation D-03.
- You prove the product is usable by **five first-time users**, move the document pages onto the new design, write the **full-cycle integration test**, and record the **final demo video**.

What the user sees from your work: screen 5 of the mockup (result and decision), the publish card inside screen 7, and the restyled document pages.

## Files you own this sprint

- New: `app/results/` (services, routes, journey), `templates/results/` (`result.html`, `_publish_card.html`, `_decision_summary.html`), `tests/results/`, `tests/integration/test_full_cycle.py`, `docs/usability/`
- Yours already: `app/documents/`, `templates/documents/`, `tests/documents/`
- Shared, yours this sprint: `app/security.py` (CSRF), `README.md` (final), `docs/demo/`
- Do not edit: `templates/base.html` and `static/css/app.css` (Varun). Ask him for the CSRF meta tag and fetch wrapper hook, or send him a small pull request to review.

---

## Issue #12 `[ADM-F-017]` Admin publish completed allotment results

**User story:** As an administrator, I want to publish the results only after I have reviewed the run, so that candidates see official results and not a half-finished state.

**Requirement (from the board):** Administrator publishes a completed allotment run; candidates can see results only after publication.

**Acceptance criteria**
- [ ] `POST /api/v1/admin/allotment/runs/<runId>/publish` and the Publish button in `templates/results/_publish_card.html` both call `results.services.publish(run_id, actor_id)`.
- [ ] Unknown run id returns 404. Publishing a run that is already published returns 409. The table `result_publications` has `UNIQUE (run_id)`, so two administrators clicking together cannot both succeed (test with two sessions).
- [ ] There is no way to publish when no run has completed (the console never shows the button; the API returns 404 or 409 with a clear message).
- [ ] Anonymous 401, candidate 403 (TC-022).
- [ ] The audit entry `results.publish` (target: the run id) is written. It appears in Tasya's audit page.
- [ ] Before publication a candidate's `/result` and API say "not published yet" (TC-017 step 1). Immediately after publication they see their result (step 3).
- [ ] The card has three states, matching the mockup: no run yet (disabled), run completed and not published (primary button with a confirmation), published (shows when and by whom, button gone).
- [ ] `_publish_card.html` takes the run as a parameter so Gagan can include it from the console page.

**Tasks:** service and route first (Day 1, test against a fake `AllotmentRun` row); the partial on Day 2 morning so Gagan can include it; confirmation dialog.
**Depends on:** the Day 1 schema PR; Gagan's `get_completed_run()`.
**Test reference:** TC-017. **Story points:** 3 | **Sprint:** 2

---

## Issue #13 `[ADM-F-018]` Candidate views the published allotment result

**User story:** As a candidate, I want to see my allotment outcome in one clear page, so that I know whether I have a seat and what to do next.

**Requirement (from the board):** After publication a candidate sees the allotted college and branch (if any) and their allocation status.

**Acceptance criteria**
- [ ] `GET /result` (page) and `GET /api/v1/allotment/result` (JSON) are for candidates only; a candidate can only ever see their own result.
- [ ] The service `candidate_view(candidate_id)` returns exactly one of four states, and the page and API show them:

| State | When | What the candidate sees |
|---|---|---|
| `NOT_PUBLISHED` | No publication for the completed run, or no run | "Results will appear here once the administrator publishes them." API: 404 |
| `NOT_IN_RUN` | Published, but this candidate has no result row (never locked, or not Eligible at run time) | "You were not part of this allotment run" with the reason if it can be known |
| `NOT_ALLOCATED` | Result row `Not Allocated` | "None of your locked choices had a seat left in your category", no college shown (TC-018 step 2) |
| `ALLOCATED` | Result row `Allocated` | The letter: college, branch, seat category, choice number out of N, exam and rank, reference number, status, decision (TC-018 step 1) |

- [ ] The letter prints cleanly: add a print stylesheet so Ctrl+P gives one page with no sidebar or buttons. This replaces any PDF feature.
- [ ] `app/results/journey.py` returns the `result` step (`locked` until published, then `done`, or `problem` for Not Allocated) and the `decision` step (see #14).
- [ ] The page uses the shared shell and the `ticket` look from the mockup.

**Tasks:** service; four templates (one page, four branches); print CSS; tests for each state and for another candidate's data never appearing.
**Depends on:** #12; Gagan's `get_result_for_candidate`; Varun's shell.
**Test reference:** TC-018. **Story points:** 3 | **Sprint:** 2

---

## Issue #14 `[ADM-F-019]` Accept or reject the allotted seat exactly once

**User story:** As a candidate with a seat, I want to accept it or reject it, once, so that my decision is recorded and cannot be changed by accident.

**Requirement (from the board):** A candidate with a published allotted seat can accept or reject/withdraw it exactly once.

**Acceptance criteria**
- [ ] `POST /api/v1/allotment/decision` with `{decision: "Accept"|"Reject"}` records `Accepted` or `Rejected`.
- [ ] A candidate who is Not Allocated or not in the run gets 422. Before publication it returns 404. Anonymous 401, administrator 403.
- [ ] The second attempt returns 409 "Your decision has already been recorded". This is backed by `UNIQUE (result_id)` in `seat_decisions`: a test sends two requests from two sessions at once and exactly one wins (TC-019 steps 2 and 3).
- [ ] The page asks for confirmation for both buttons ("You can decide only once"), then shows the decision and hides the buttons.
- [ ] A rejected or withdrawn seat is not released and nobody is re-allotted (SAD A-12). The page says so.
- [ ] `_decision_summary.html` shows counts of Accepted, Rejected and Undecided for Gagan's console.
- [ ] The decision is visible on the candidate dashboard's `decision` step.

**Tasks:** service with the database rule; route; page buttons and dialogs; tests including the concurrent one.
**Depends on:** #13. **Test reference:** TC-019. **Story points:** 3 | **Sprint:** 2

---

## Issue D5 (new): CSRF protection for every state-changing request

**Title:** `[D-03] Central CSRF check for all forms and API calls`

**User story:** As the institution, we want a page on another website to be unable to submit actions on a signed-in user's behalf, so that candidate and administrator data stays safe.

**Requirement:** Test Plan addendum ("keep CSRF protection"); SAD A-02; DEVIATIONS D-03 and P-06; decision D2-13.

**Acceptance criteria**
- [ ] One check in `app/security.py` refuses every `POST`, `PUT`, `PATCH` and `DELETE` without a valid token with 400 and a clear message, for both HTML forms (hidden field `csrf_token`) and JSON calls (header `X-CSRF-Token`).
- [ ] The token is tied to the browser session and works for logged-out forms too (login and register). No new dependency.
- [ ] The base template exposes the token (`<meta name="csrf-token">`) and a small script adds the header to every `fetch` call that is not a GET. The existing logout, login, register, profile and exam-details scripts keep working.
- [ ] Every HTML form in the product carries the token: application, documents upload and resubmit and review, catalogue forms, rules page, correction form, choices, decision, publish. A test lists every `<form method="post">` in the rendered pages and fails if one has no token field.
- [ ] The existing document tokens keep working or are replaced by the central one; no page gets two different token fields.
- [ ] The check is disabled when `TESTING` is on, so the existing 440+ tests are unchanged. A dedicated `tests/security/test_csrf.py` turns it on and proves: missing token 400, wrong token 400, correct token works, GET and HEAD are not affected, a form posted from a page with no token (simulating another site) is refused, and the API accepts the header.
- [ ] D-03 is marked closed (Gagan edits DEVIATIONS).

**Tasks:** Day 1: check, token helper and tests (no template changes yet). Day 2: after Varun's shell is merged, add the meta tag and fetch wrapper and the hidden fields. Merge as a small number of pull requests, not one big one.
**Depends on:** Varun's shell (Day 2 part). **Test reference:** SEC-F-001 and SEC-F-002 (supporting TC-021, TC-022). **Story points:** 5 | **Sprint:** 2

---

## Issue #15 `[ADM-NFR-004]` Validate application usability with first-time users

**User story:** As the team, we want to see real first-time users complete an application without help, so that we know the interface works for the people it is for.

**Requirement (from the board):** A first-time user can complete application submission without external assistance.

**Acceptance criteria**
- [ ] `docs/usability/SCRIPT.md` has the task script (register, enter exam details, fill and submit the application, find the reference number), what you say and do not say, what counts as "completed without help", and an observation sheet (time, where they hesitated, what they said).
- [ ] At least **five** people who have never used the application and are not team members try it, one at a time, with no briefing, on the build that has the new design (late Day 2 or Day 3 morning).
- [ ] At least 3 of 5 complete application submission unaided (Test Plan TC-029 expectation). If fewer do, record that honestly.
- [ ] The three most common difficulties are fixed (or filed as defects with a severity) and noted.
- [ ] `docs/evidence/usability.md` records participants as P1 to P5 (no names), completion, time taken and difficulties.

**Tasks:** Day 1: write the script and book five people for specific time slots. Day 2 evening and Day 3 morning: run the sessions on the same laptop. Day 3: fixes and the report.
**Depends on:** Varun's shell and dashboard on `main`. **Test reference:** TC-029. **Story points:** 3 | **Sprint:** 2

---

## Issue D6 (new): Documents pages on the shared design, with journey status

**Title:** `[ADM-F-008] Document pages on the shared design; documents step for the dashboard`

**User story:** As a candidate I want my document page to show clearly what is approved, pending or rejected and why, and as an administrator I want to review quickly with names in front of me.

**Requirement:** ADM-F-007, ADM-F-008; ADM-NFR-004.

**Acceptance criteria**
- [ ] `/documents/upload`, `/documents` and `/admin/documents` use the shared components: status pills ("Pending Verification" shown for `Pending`), a callout with the administrator's rejection reason, an inline "Upload a new copy" for rejected documents.
- [ ] The administrator queue shows candidate **name** and reference, document type and upload time, a Download link, and Approve and Reject with the reason required for Reject.
- [ ] `app/documents/journey.py` returns the `documents` step: `locked` until the application is Submitted (detail says why), `current` while fewer than three uploaded, `waiting` while any is Pending, `problem` if any is Rejected, `done` when all three are Approved.
- [ ] All existing document tests still pass (upload type and size limits, review, resubmission, the foreign keys and the upgrade command).

**Depends on:** Varun's shell. **Test reference:** TC-006, TC-007, TC-008. **Story points:** 2 | **Sprint:** 2

---

## Issue D7 (new): Full-cycle integration test, from registration to seat decision

**Title:** `[ADM-F-019] One automated test that walks the whole cycle`

**User story:** As the team, we want a single test that behaves like a candidate and an administrator from registration to the seat decision, so that any later change that breaks the product is caught immediately.

**Requirement:** Test Plan section 5 (system tests, "end-to-end workflows from registration through seat decision, for both Candidate and Administrator roles").

**Acceptance criteria**
- [ ] `tests/integration/test_full_cycle.py` uses real routes, real logins and generated fictional files against a temporary database seeded like `seed-db`, with no `xfail`.
- [ ] Steps, each asserted: register with date of birth (duplicate refused); log in and land on the dashboard; save exam details; save a draft, log out and in; submit and receive `ADM-YYYY-NNNNNN`; upload three documents; the administrator rejects one with a reason and approves the others; the candidate resubmits and it is approved; eligibility is Eligible with a reason; add, reorder and lock choices; a second candidate who never locks; the administrator runs allotment; before publication the candidate sees "not published"; publish; the candidate sees the allotted seat; accept; a second decision is refused; the audit log shows document, allotment and publish entries; a candidate gets 403 on every admin route.
- [ ] A second smaller test uses the Test Plan oracle through the pages: five candidates, the expected seats, C4 and C5 Not Allocated.
- [ ] Runs in under 30 seconds and is part of the normal CI run.

**Tasks:** build helper functions (register, approve all documents, make eligible) so the test reads like the story; use the demo sample files that `docs/sprint1-final` brings; add pieces as each module lands on Day 2.
**Depends on:** everyone's modules merged (build it step by step from Day 1). **Test reference:** TC-001 to TC-025 as a system test. **Story points:** 3 | **Sprint:** 2

---

## Issue D8 (new): Final demo script, video and README

**Title:** `[DOC] Final demo walkthrough, video and README`

**User story:** As an evaluator, I want to see the complete product in a short video and be able to run it myself from the README, so that I can verify the project.

**Acceptance criteria**
- [ ] `docs/demo/VIDEO_SCRIPT.md` (from the Sprint One script) covers the whole cycle in the order of the Sprint Two demonstration, with the exact clicks and what to say, and names the demo data it uses (the 300 candidate dataset for the administrator views, one fresh candidate for the live walkthrough).
- [ ] The video shows: registration to dashboard, application and documents, administrator verification, eligibility, choices and lock, the allotment console and consistency check, publish, the candidate's result and decision, the audit log, HTTPS padlock warning explained.
- [ ] The README has correct clone and run steps (no stale branch), the HTTPS steps, the demo reset, the test commands and a short feature list per role. Everything stale about Sprint One is removed.
- [ ] A person who has not seen the project follows the README on a clean clone and reaches the demo (ask a teammate).

**Depends on:** all features frozen (Day 3 noon). **Story points:** 2 | **Sprint:** 2

---

## Your evidence

Record on `main`, with command, result and date: **TC-006, 007, 008, 017, 018, 019, 029**. Your Sprint One file `docs/evidence/dikshith.md` already covers 006, 007, 008; re-run them after the Sprint Two merges because the pages were restyled.

## Day checklist

**Day 1** [ ] results services tested on fake rows  [ ] CSRF check and tests (server side)  [ ] five people booked, script written  [ ] full-cycle test skeleton
**Day 2** [ ] publish card in Gagan's console  [ ] `/result` and decision  [ ] CSRF in templates  [ ] documents pages restyled  [ ] first usability sessions
**Day 3** [ ] usability finished and fixed  [ ] full-cycle test green  [ ] evidence for seven cases  [ ] video and README after the noon freeze

## What you need from others and what you owe them

| You need | From | By |
|---|---|---|
| Contracts and schema PR | Gagan | Day 1 morning |
| `get_completed_run`, `get_result_for_candidate` working | Gagan | Day 1 evening |
| Shell, meta tag hook | Varun | Day 1 evening |

| You give | To | By |
|---|---|---|
| `_publish_card.html` and `_decision_summary.html` | Gagan | Day 2 morning |
| `results/journey.py` (two steps) | Varun's dashboard | Day 2 |
| The CSRF fetch wrapper snippet | Varun | Day 2 morning |

## Watch out

- A rejected seat is not released. Say so on the page so nobody asks why the seat did not go to the next candidate.
- The existing document forms already use their own session tokens. Do not break them while you add the central check; migrate them last.
- Two clicks on "Accept" at the same moment must produce one decision and one error, not two decisions. The database key is what guarantees it, so test it through the database, not only through the button.
