# Sprint Two brief: Tasya (administrator experience, audit, test data and measurement)

Read `SPRINT_TWO_START_HERE.md` first. This file is only your part.

## Your part of the final product

You make the administrator side complete and trustworthy, and you give the whole team the test data and measurements the Test Plan asks for.

- The administrator opens a **dashboard** that says which stage the admission cycle is in, with correct numbers and names instead of ids.
- They can **find any candidate** and open their record.
- They can **change the eligibility cut-offs** without touching code (ADM-NFR-005).
- Every privileged action, including the allotment run and publication done by Gagan's and Dikshith's code, shows up in an **audit log** that cannot be edited.
- You build the **300 candidate dataset** that Gagan's performance and consistency tests and your own response-time test run on, and you compile the **Test Summary Report**.

What the user sees from your work: screens 3 and 6 of the mockup (eligibility, administrator dashboard), plus the candidate list, rules page and audit log.

## Files you own this sprint

- Yours already: `app/eligibility/`, `app/catalogue/`, `app/audit/`, `app/admin/`, their templates and tests
- New: `scripts/make_demo_dataset.py`, `scripts/measure_response_times.py`, `templates/admin/candidates*.html`, `templates/eligibility/rules.html`, `tests/admin/`, `tests/scripts/`
- `docs/TEST_SUMMARY_REPORT.md`, the RTM update in `SRS_Draft.md` section 8
- Do not edit: `templates/base.html` and `static/css/app.css` (Varun). Put page-specific CSS in your own `static/css/admin.css` using the shared tokens.

---

## Do first (30 minutes): audit entries inside someone else's transaction

Gagan's allotment run must write its audit entry in the same transaction as the seat changes (SAD A-07). `record_audit` commits by itself today. Add a keyword `commit=True` to `record_audit` and `record_admin_action` in `app/audit/services.py`: with `commit=False` it adds the row to the session and does not commit. Existing callers are unchanged. Add a test for both modes. Tell Gagan when it is merged.

---

## Issue T1 (new): Demo dataset generator, about 300 fictional candidates

**Title:** `[ADM-NFR-002] [ADM-NFR-003] Generate a 300 candidate dataset for scale, consistency and response-time tests`

**User story:** As the team, we want one command that builds a realistic dataset, so that the allotment performance, seat consistency and response-time tests all run on the same believable data.

**Requirement:** Test Plan section 6 and TC-028 precondition ("full seeded dataset, about 300 candidates, locked choices"); TC-027 (double the volume).

**Acceptance criteria**
- [ ] `python scripts/make_demo_dataset.py --candidates 300 --seed 1` fills the configured database. `--candidates 600` doubles it. The same `--seed` gives the same data.
- [ ] Idempotent: running it twice adds no duplicates (use stable emails such as `cand0001@example.test`).
- [ ] Everything is fictional and nothing secret is committed. The shared candidate password comes from the environment variable `DEMO_CANDIDATE_PASSWORD`; the script refuses to run without it. Hash it once and reuse the hash (password hashing is slow; 300 separate hashes would take minutes). The script says this in a comment, because normally each user has a different salt.
- [ ] New exam records are created as needed, respecting the unique key (`exam_type`, `rank`), with ranks spread so about 10% fall above their category cut-off (Not Eligible).
- [ ] Each candidate has a Submitted application with a reference number (use `application.services.make_reference_number`), three documents, and for most candidates a locked choice list of 3 to 6 branches. The mix is roughly: 70% fully approved and locked, 10% not eligible, 10% documents still pending or one rejected, 10% eligible but not locked.
- [ ] The seat matrix stays the Sprint One seed (240 seats in 6 branches) so there is real competition: 300 candidates against 240 seats means some will be Not Allocated.
- [ ] Build time under 1 minute for 600 candidates (use bulk inserts, not one commit per row).
- [ ] A test builds 20 candidates into a temporary database and checks the counts of each group.
- [ ] No database file, upload or password ever ends up in Git.

**Tasks:** read how `app/accounts/seed.py`, `app/catalogue/seed.py` and `app/eligibility/seed.py` create their rows and reuse their helpers; create tiny placeholder files for the document rows (or copy one valid sample PDF from `docs/demo/sample_files` once that branch is merged) so the administrator's "Download" works in the demo.
**Depends on:** Day 1 schema PR (for the choices tables).
**Needed by:** Gagan (#7, #8) from Day 1 evening; your own #29.
**Test reference:** TC-027, TC-028 (preconditions), TC-026. **Story points:** 3 | **Sprint:** 2

---

## Issue #30 `[ADM-NFR-005]` Configure catalogue, seats and eligibility rules through the admin UI

**User story:** As an administrator, I want to change the eligibility cut-off for a category, and add a college or branch, using only the admin screens, so that no code change or redeploy is needed to adapt the data.

**Requirement (from the board):** College, branch, seat-matrix and eligibility-rule data are configurable through admin interfaces rather than hardcoded.

**Acceptance criteria**
- [ ] `/admin/eligibility-rules` lists the five categories with cut-off rank and an Active switch. A category that has no rule shows "No rule" and a Create button.
- [ ] The administrator can edit a cut-off (whole number greater than 0) and switch a rule on or off. Invalid input shows an inline error and changes nothing.
- [ ] Each change is written to the audit log as `rule.create` or `rule.update` with the rule id (never the candidate data).
- [ ] The new value is used by the next eligibility check straight away. Test: a candidate with rank 21,000 in General is Not Eligible with cut-off 20,000; after the administrator raises it to 25,000 the same candidate is Eligible.
- [ ] A switched-off rule gives Not Eligible with the existing message "No active eligibility rule exists for the category ...".
- [ ] Anonymous 401, candidate 403 (TC-022). The page uses the shared shell.
- [ ] **TC-030 end to end:** an integration test uses only HTTP calls as the administrator to add a new college, a branch, seat capacity and change a rule; then as a candidate it appears in `/colleges`, can be added in `/choices`, and is used by the allotment, with no source change. Once Varun's and Gagan's parts merge, run it for real and keep it as a test.

**Tasks:** list and edit page; service functions in `app/eligibility/services.py` (`list_rules`, `update_rule`, `create_rule`); audit calls; tests; the TC-030 integration test on Day 3.
**Depends on:** #28 audit flag, Varun's shell (page style only). **Test reference:** TC-030, TC-009. **Story points:** 5 | **Sprint:** 2
Keep #30 In Progress until the TC-030 integration run passes.

---

## Issue #28 `[SEC-F-005]` Record and display audit logs for privileged admin actions

**User story:** As an administrator, I want a read-only log of everything privileged that happened, with who did it and when, so that the admission is traceable.

**Requirement (from the board):** Audit entries with actor, timestamp and action type exist for privileged actions and are visible to administrators; they cannot be edited through the UI.

**Acceptance criteria**
- [ ] New actions logged: `rule.create`, `rule.update` (your page) and `candidate.update` (your candidate screen). Existing catalogue and document actions keep working.
- [ ] Gagan's `allotment.run` and Dikshith's `results.publish` appear in the log (cross-check test once both are merged). A failed run appears with outcome `Failed`.
- [ ] The audit page shows newest first, 50 per page, with filters for action type and actor, the actor's **name** (joined from users by `actor_id`) and a readable target such as "College: Meridian Institute of Technology". A deleted record must not break the page (the log has no foreign key on purpose).
- [ ] The JSON endpoint `/admin/audit-logs.json` keeps its current shape.
- [ ] There is still no POST, PUT or DELETE route under the audit blueprint (a test walks `app.url_map` to prove it) and the existing database triggers still reject `UPDATE` and `DELETE`.
- [ ] No names, emails, mobile numbers or rejection reasons are stored in any audit entry.
- [ ] TC-025: evidence shows one entry per action for a seat-matrix edit, the allotment run and publication, and that no edit or delete path exists.

**Tasks:** `commit` flag (above); new action calls; page and filters; the `url_map` test; the cross-module test after Day 2 merges.
**Depends on:** Gagan's run and Dikshith's publish for the last two criteria. **Test reference:** TC-025. **Story points:** 5 | **Sprint:** 2
Keep #28 In Progress until `allotment.run` and `results.publish` are both visible.

---

## Issue T4 (new): Administrator dashboard v2 and candidate records

**Title:** `[ADM-F-020] Dashboard with cycle stage, names and queues; candidate list and record`

**User story:** As an administrator, I want a dashboard that shows where the admission cycle stands and a way to find and open any candidate, so that I can manage the process without querying the database.

**Requirement:** ADM-F-020; SAD 4.3.7 (`GET /admin/dashboard`, `GET /admin/candidates`, `GET /admin/candidates/{id}`, `PUT /admin/candidates/{id}`); SAD A-18; decision D2-12.

**Acceptance criteria**
- [ ] The dashboard shows a cycle banner (verification and choice filling, then allotment run, then published) read from `allotment.services.get_completed_run()` and `results.services`, plus tiles: registered candidates, submitted applications, documents pending and rejected, Eligible and Not Eligible, choices locked. Every number matches the database (TC-020 step 2; write the test that compares them to direct counts).
- [ ] The verification queue shows candidate **name and reference number**, document type and time, with a Review link; no raw ids.
- [ ] `/admin/dashboard.json` keeps its current keys (existing tests rely on them); new keys are added, none removed.
- [ ] `/admin/candidates` lists candidates with search (name, email, mobile, reference), filters (application status, eligibility, locked) and paging (50 per page). With 300 candidates the page renders in under 2 seconds: do not call `get_eligibility` once per row with separate queries; compute for the visible page only.
- [ ] `/admin/candidates/<id>` shows profile, exam details, application, documents, eligibility, choices and result, read-only except the correction form.
- [ ] The correction form changes **name and mobile only** (D2-12), validates like registration (including the duplicate mobile 409), and writes `candidate.update`. It never shows or returns a password hash.
- [ ] Anonymous 401, candidate 403, on the pages and the JSON.

**Tasks:** extend `app/admin/services.py`; routes and templates; tests (counts match, names shown, correction audited, 403s); check the 300 candidate page time with T1's dataset.
**Depends on:** Varun's shell, T1, Gagan's and Dikshith's service functions (stubs are fine until they land).
**Test reference:** TC-020. **Story points:** 5 | **Sprint:** 2

---

## Issue #29 `[ADM-NFR-001]` Verify candidate page response times within two seconds

**User story:** As the team, we want measured proof that the pages candidates use respond within two seconds, so that the performance requirement is evidenced and not assumed.

**Requirement (from the board):** Standard candidate-facing page requests respond within 2 seconds under normal load in the demonstration environment.

**Acceptance criteria**
- [ ] A small timing hook (`before_app_request` and `after_app_request` in your admin blueprint, so no shared file changes) logs `method path status milliseconds user_id role` for every request and adds an `X-Response-Time` header. It never logs email, mobile, passwords, cookies or document contents (SAD 4.4).
- [ ] `scripts/measure_response_times.py` simulates 25 concurrent candidates (threads are enough; JMeter is optional) doing sign in, dashboard, catalogue and choices pages against the 300 candidate dataset, and prints average, 95th percentile and maximum per page.
- [ ] The average for standard pages is at most 2 seconds. Sign-in includes password hashing, so report it separately and say so.
- [ ] If SQLite locking causes errors or slow pages under 25 users, record the numbers honestly and fix the cause (index, query, fewer commits) or explain the limit.
- [ ] Results go in `docs/evidence/tasya.md` with the date, machine, dataset size and command.

**Depends on:** T1, Varun's dashboard and choices pages (measure the sign-in and catalogue pages earlier if they are not ready).
**Test reference:** TC-026. **Story points:** 3 | **Sprint:** 2

---

## Issue T6 (new): Eligibility page, catalogue and admin pages on the shared design; catalogue needs login

**Title:** `[ADM-F-009] [ADM-F-010] [SEC-F-001] Eligibility checklist, restyled catalogue and admin pages, login-only catalogue`

**User story:** As a candidate I want the eligibility page to show exactly why I am Pending, Eligible or Not Eligible, and as the institution we want the catalogue to be visible only to signed-in users.

**Requirement:** ADM-F-009 ("human-readable reason"); SAD access matrix (catalogue: candidate and administrator only); SEC-F-001; decision D2-10, D2-14.

**Acceptance criteria**
- [ ] `/colleges` redirects anonymous visitors to the login page and works for candidates and administrators. `tests/catalogue/test_candidate.py` opens it without logging in in about a dozen places; give those tests a signed-in client and add one test that anonymous is redirected.
- [ ] The eligibility page shows the result (pill and sentence) and a checklist as in the mockup: exam details entered, application submitted, three documents approved (with the count), rank within the cut-off (with both numbers). Pending is displayed as "Pending Verification".
- [ ] `app/eligibility/journey.py` returns the `eligibility` step: `waiting` while documents are pending, `problem` when Not Eligible (reason in `detail`), `done` when Eligible.
- [ ] The three decision cases still pass their tests: Eligible, Not Eligible, Pending (TC-009).
- [ ] The catalogue pages (candidate list, admin list, forms), the audit page and the dashboard use the shared components; the catalogue `_styles.html` include is removed when your pages no longer need it.

**Depends on:** Varun's shell. **Test reference:** TC-009, TC-010, TC-021. **Story points:** 3 | **Sprint:** 2

---

## Your evidence and the final report

1. Day 1: get PR #58 (your Sprint One evidence) reviewed and merged first, so the file is on `main`.
2. Record on `main`, with command, result and date: **TC-009, 010, 011, 020, 025, 026, 030**.
3. Day 3: compile `docs/TEST_SUMMARY_REPORT.md` from everyone's evidence (due 15:00): number executed and passed out of 30, defects by severity, requirement coverage out of 30 (Test Plan section 14), oracle result and seat consistency result from Gagan.
4. Update the RTM table in `SRS_Draft.md` section 8 from "Planned" to "Verified" only where evidence exists, and note it in `DOCUMENT_CHANGE_RECORD.md`.

## Day checklist

**Day 1** [ ] `commit` flag merged and announced  [ ] PR #58 merged  [ ] dataset script  [ ] rules page working
**Day 2** [ ] dashboard v2, candidate list and record  [ ] audit page and new actions  [ ] timing hook  [ ] T6
**Day 3** [ ] TC-030 end to end, #29 measurement, evidence for seven cases  [ ] Test Summary Report and RTM  [ ] bug fixing

## What you need from others and what you owe them

| You need | From | By |
|---|---|---|
| Contracts and schema PR | Gagan | Day 1 morning |
| Shell and macros | Varun | Day 1 evening |
| `allotment.run` and `results.publish` audit calls | Gagan, Dikshith | Day 2 |

| You give | To | By |
|---|---|---|
| `record_audit(commit=False)` | Gagan | Day 1, first 30 minutes |
| Dataset script | Gagan | Day 1 evening |
| `eligibility/journey.py` | Varun's dashboard | Day 2 |
| Evidence files for the report | You, then everyone sends you theirs | Day 3, 15:00 |

## Watch out

- The five categories are fixed by a database CHECK on `eligibility_rules`; "add a rule" only means creating a rule for a category that has none.
- The audit table has no foreign keys by design and its triggers block `UPDATE` and `DELETE`. Do not try to "clean up" test data in it; use a fresh temporary database in tests, as the existing audit tests do.
- Rejection reasons and names must stay out of audit rows; the document review code already follows this, copy that habit.
