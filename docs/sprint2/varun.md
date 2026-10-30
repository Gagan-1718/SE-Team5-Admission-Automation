# Sprint Two brief: Varun (choices, design system, candidate dashboard)

Read `SPRINT_TWO_START_HERE.md` first. This file is only your part.

## Your part of the final product

You own what the candidate feels. Two things:

1. **The look of the whole product.** One shell (sidebar, top bar, flash messages), one set of components and one stylesheet that every other person's pages move onto on Day 2. Your Sprint One login and register polish is the starting point; the mockup in `docs/design/final-product-mockup.html` has the tokens and component CSS ready to lift.
2. **The candidate's journey.** The dashboard that shows where they are and what to do next, and the choice-filling module: add, reorder and lock their preferred colleges.

What the user sees from your work: screens 1, 2 and 4 of the mockup (sign in, dashboard, choice filling).

## Files you own this sprint

- New: `app/choices/` (services, routes, journey), `templates/choices/`, `templates/dashboard/`, `tests/choices/`, `templates/_ui.html` (macros), `static/css/app.css`
- Shared, yours this sprint: `templates/base.html`, `templates/home.html`, error pages
- Yours already: `app/accounts/`, `templates/accounts/`, `tests/accounts/`
- Do not edit other people's module code. Their pages move onto your shell themselves on Day 2.

---

## Issue V1 (new): One design system and app shell for every page

**Title:** `[ADM-NFR-004] Shared design system, app shell and error pages`

**User story:** As any user, I want every page to look and behave the same way, so that I never feel lost and the product feels finished.

**Requirement:** SRS 3.1 (responsive, distinct candidate and administrator views); SAD 4.5 and A-22 (guided flow, confirmations, basic accessibility); ADM-NFR-004.

**Acceptance criteria**
- [ ] `static/css/app.css` defines the tokens from the mockup (`--ink`, `--brand`, `--paper`, `--ok`, `--wait`, `--bad`, `--idle` and their washes) and the components listed below. No web fonts, no CDN, no JavaScript framework: the lab may be offline.
- [ ] `templates/base.html` renders a role-aware sidebar. Candidate: Dashboard, Profile and exam, Application, Documents, Eligibility, Choices, Result, Colleges; steps that are not available yet show a lock and the reason on hover or focus. Administrator: Dashboard, Candidates, Documents, Colleges and seats, Eligibility rules, Run and publish, Audit log. Anonymous visitors get a plain top bar with Log in and Register.
- [ ] `templates/_ui.html` provides macros: `page_header`, `card`, `tile`, `pill(status)`, `callout(kind)`, `stepper`, `empty_state`, `field(label, error)`, `confirm_dialog`, `data_table`.
- [ ] One helper turns stored statuses into display words, including `Pending` → "Pending Verification" (D-06). Used by `pill`.
- [ ] Friendly 403, 404 and 500 pages, no stack trace, with a link back to the right home page.
- [ ] Works down to a 400 px wide screen; every control reachable by keyboard with a visible focus ring; every input has a label.
- [ ] The old stylesheets (`site.css`, `accounts.css`, the catalogue `_styles.html`) stay loaded until their owners migrate, so no existing page breaks on the day you merge.
- [ ] `tests/test_navigation.py` is updated, not deleted, and passes: it reads the nav links of the base template. Add tests for the admin nav, the locked-step nav and the error pages.
- [ ] Login, register, profile and the landing page use the new components. The landing page replaces the "Sprint One" placeholder text with the product story and Log in / Register buttons.

**Tasks**
- [ ] Branch `feature/design-system`. Lift the `:root` block and the `.app`, `.side`, `.card`, `.pill`, `.callout`, `.stepper`, `.btn`, `.field`, `.t` rules from the mockup into `static/css/app.css`.
- [ ] Build the shell and macros; swap `base.html`; confirm every existing page still renders (open each in the browser).
- [ ] Post in the group chat with a 5-line "how to use the shell" note (extend `base.html`, use `page_header`, use `pill`, put your own CSS in `static/css/<module>.css`).
- [ ] Open the pull request early (Day 1 midday) and merge as soon as it is reviewed. Polishing the landing page can follow.

**Depends on:** nothing. **Blocks:** everyone's Day 2 restyle.
**Test reference:** supports TC-029 (usability). **Story points:** 5 | **Sprint:** 2
**Target:** shell merged by end of Day 1.

---

## Issue #21 `[ADM-F-012]` Add, remove and preview choices without duplicates

**User story:** As an eligible candidate, I want to add colleges and branches to a list and see it, so that I can plan where I would like a seat.

**Requirement (from the board):** Eligible candidates add and remove college-branch choices and preview them; duplicate choices are rejected.

**Acceptance criteria**
- [ ] Only a logged-in Eligible candidate can add. Pending or Not Eligible candidates get 403 on the API and, on the page, an explanation with the eligibility reason and a link to `/eligibility` (TC-012 step 4). Anonymous 401 or redirect; administrator 403.
- [ ] Adding a branch gives it the next priority (last + 1). Adding a branch already in the list returns 409 with "That branch is already in your list" and the database unique key (`candidate_id`, `branch_id`) backs it up.
- [ ] An unknown branch id returns 404 and creates nothing.
- [ ] Removing a choice renumbers the rest so priorities are 1..n with no gaps (TC-012 step 2).
- [ ] The preview lists college, city, branch, priority and **seats left in the candidate's own category** from the catalogue. A branch with 0 seats left in that category can still be added, with a visible warning (D2-04).
- [ ] A candidate can only see and change their own list; another candidate's choice id gets 404 or 403.
- [ ] Once locked, add and remove return 409 (see #23).
- [ ] JSON API: `GET /api/v1/choices` (list and `locked` flag), `POST /api/v1/choices` `{collegeId, branchId}`, `DELETE /api/v1/choices/<id>`.

**Tasks**
- [ ] Day 1: `app/choices/services.py` exactly as in the start guide section 4.3 (names matter, Gagan calls two of them), then routes, then tests.
- [ ] Day 1: `get_locked_branch_ids` and `locked_candidate_ids` must work by end of Day 1 (Gagan's run needs them on Day 2).
- [ ] Day 2: `/choices` page: search box on the left, my list on the right, as in the mockup. Reuse `catalogue.services.list_catalogue(query=...)` for the search; do not copy catalogue code.
- [ ] Tests for every error path in the start guide's error table.

**Depends on:** ADM-F-009 (done), ADM-F-010 (done), Day 1 schema PR.
**Test reference:** TC-012. **Story points:** 5 | **Sprint:** 2

---

## Issue #22 `[ADM-F-013]` Reorder and persist choice preferences

**User story:** As a candidate, I want to move my choices up and down, so that my list reflects what I want most.

**Requirement (from the board):** Candidates reorder saved choices before locking; the order is saved.

**Acceptance criteria**
- [ ] `PUT /api/v1/choices/order` with `{orderedChoiceIds: [...]}` saves the new order. The ids must be exactly the candidate's current choices, no more and no fewer, otherwise 400 and nothing changes.
- [ ] After the change priorities are 1..n and the list is returned in the new order.
- [ ] The order is still there after logging out and in (TC-013).
- [ ] Locked list: 409, nothing changes (#23).
- [ ] The page has Up and Down buttons (drag and drop is optional) reachable by keyboard, announced to screen readers ("Moved to position 2"), and saves without a full page reload.

**Tasks:** service `reorder`; route; tests for a mismatched id list, a duplicate id in the list, another candidate's id, and persistence across a second client session; page buttons.
**Depends on:** #21. **Test reference:** TC-013. **Story points:** 3 | **Sprint:** 2

---

## Issue #23 `[ADM-F-014]` Lock choices and prevent UI and API modifications

**User story:** As a candidate, I want to lock my list when I am sure, so that my final preferences are the ones used for allotment.

**Requirement (from the board):** Locking freezes the list; no add, remove or reorder is possible afterwards, in the page or through the API.

**Acceptance criteria**
- [ ] `POST /api/v1/choices/lock` locks the list and records the time. A list with no choices returns 422 "Add at least one choice first". Locking twice returns 409.
- [ ] After locking, add, remove and reorder are refused with 409 **in the API and in the page** (TC-014 step 2 tries both).
- [ ] There is no unlock route for anyone, including the administrator (D2-03).
- [ ] The page asks for confirmation ("Locking is final. Allotment uses this exact order.") before it calls the API, and afterwards shows "Locked on <date>" with the list read-only.
- [ ] `get_locked_branch_ids(candidate_id)` returns the branch ids in priority order for a locked list and `[]` for an open one; `locked_candidate_ids()` returns exactly the candidates with a lock row.
- [ ] `app/choices/journey.py` reports the `choices` step: `locked` with the reason while not Eligible, `current` while open, `done` once locked.

**Tasks:** `choice_locks` row; guard inside every mutating service function (not only the routes); route; confirm dialog from your own shell; tests for each refusal.
**Depends on:** #22. **Test reference:** TC-014. **Story points:** 3 | **Sprint:** 2

---

## Issue V5 (new): Candidate dashboard with guided step tracker

**Title:** `[ADM-NFR-004] Candidate dashboard with step tracker and next-step prompt`

**User story:** As a candidate, I want a home page that shows where I am in the process and tells me the one thing to do next, so that I can finish my application without asking anyone.

**Requirement:** TC-002 ("redirected to dashboard"); SAD 4.5 step tracker; A-22; ADM-NFR-004.

**Acceptance criteria**
- [ ] `/dashboard` is for candidates only (anonymous redirected to login, administrator 403).
- [ ] The page builds itself only from `step_statuses(candidate_id)` of the six journey modules (start guide 4.4). It reads no other module's tables.
- [ ] It shows, in order: Profile and exam details, Application, Documents, Eligibility, Choices, Allotment result, Seat decision, each with a state pill and a one-line detail.
- [ ] One prominent callout shows the first step in state `problem`, otherwise the first in `current`, with a button to its `href`.
- [ ] Tiles show exam and rank, application status and reference, documents approved out of three, and eligibility.
- [ ] After login a candidate lands on `/dashboard` and an administrator on `/admin/dashboard` (D2-11); the `next` parameter on the login page is still honoured.
- [ ] Tests feed fake step lists for each situation: brand new user, rejected document, waiting for eligibility, Eligible and choices open, locked, result published and allotted.
- [ ] Works while other modules are still stubs (the Day 1 stubs return `locked`).

**Tasks:** page and template; tests with monkeypatched `step_statuses`; login redirect (the JavaScript in `templates/accounts/login.html` decides the redirect today); keep `tests/accounts/` green.
**Depends on:** V1 shell; every owner's `journey.py` (stubs on Day 1, real on Day 2).
**Test reference:** TC-002, supports TC-029. **Story points:** 5 | **Sprint:** 2

---

## Issue V6 (new): Date of birth, address and exam-details freeze

**Title:** `[ADM-F-001] [ADM-F-003] Collect date of birth and address; freeze exam details after submission`

**User story:** As a candidate I want to give my date of birth when I register and my address on my profile, as the requirements say; and as the institution we want rank and category to stay fixed once an application is submitted, so that nobody can change their rank after their documents are approved.

**Requirement:** ADM-F-001 and TC-001 (date of birth is a registration field); ADM-F-003 ("contact details, address"); DEVIATIONS D-05; decision D2-01.

**Acceptance criteria**
- [ ] Registration form and API require a date of birth (a real date in the past). A missing or invalid value returns the same field-level style of error as the other fields (TC-001 step 4).
- [ ] The profile has address fields (address line, city, 6-digit pincode) that can be saved and are shown on the page (TC-003 step 1).
- [ ] Once the candidate's application is Submitted, `PUT /accounts/exam-details` returns 409 "Exam details are locked after you submit your application", and the profile page shows the exam details read-only with that explanation. Before submission it works exactly as today. Use `application.services.get_submitted_application`; do not read the applications table.
- [ ] New columns on `users`: because `init-db` does not alter existing tables, everyone resets once (D2-15). If you prefer a safe upgrade, follow the pattern of `_ensure_exam_record_column` in `app/accounts/seed.py`.
- [ ] Existing registration, login, profile and exam tests are updated for the new required field and still pass. Duplicate email or mobile still returns 409.
- [ ] DEVIATIONS D-05 is marked closed by Gagan when this merges.

**Tasks:** model columns; validation; form fields; the freeze check; tests; tell Gagan so he can update D-05.
**Depends on:** Day 1 schema PR (no dependency on tables, but resetting the database together is easier then).
**Test reference:** TC-001, TC-003. **Story points:** 3 | **Sprint:** 2

---

## Your evidence (not an issue)

The TC table at the top of your `docs/evidence/varun.md` still shows FAIL rows from a run made before the other modules were merged; the "corrected run" below it was made on Python 3.11.9, not the team's 3.12. On Day 3, after everything is on `main`, replace the table with a fresh run on Python 3.12 against `main` for **TC-001, 002, 003, 012, 013, 014, 021, 022, 023**: command, result, date. Add one line each for the mobile (400 px) and keyboard-only pass. A case that fails is recorded as failed and logged in `docs/DEFECT_LOG.md`.

## Day checklist

**Day 1** [ ] shell merged  [ ] choice services and API with tests  [ ] `get_locked_branch_ids` and `locked_candidate_ids` working  [ ] `journey.py` stubs agreed
**Day 2** [ ] `/choices` page with lock dialog  [ ] dashboard and login redirect  [ ] V6  [ ] accounts and landing pages on the new shell
**Day 3** [ ] evidence for nine cases  [ ] mobile, keyboard and contrast pass  [ ] bug fixing

## What you need from others and what you owe them

| You need | From | By |
|---|---|---|
| Contracts and schema PR | Gagan | Day 1 morning |
| `step_statuses` in each module | Gagan, Dikshith, Tasya | Day 2 (stubs on Day 1) |
| `get_eligibility` (exists) | Tasya | now |

| You give | To | By |
|---|---|---|
| Shell, macros and a 5-line how-to | Everyone | Day 1 evening |
| Choice service functions working | Gagan | Day 1 evening |
| Dashboard route and login redirect | Everyone (for demo) | Day 2 |

## Watch out

- Changing `base.html` changes every page at once. Open each existing page after your change, not only your own.
- `tests/test_navigation.py` parses the nav with a regular expression: keep real `<a href>` links in the sidebar (not buttons or JavaScript-only links).
- The logout button today is a JavaScript `fetch`. If you add CSRF to it (Dikshith adds the token helper), keep it working without a full page reload.
- Show names and references on screen, never raw database ids.
