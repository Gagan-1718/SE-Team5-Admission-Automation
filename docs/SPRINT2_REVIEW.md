# Sprint Two review and retrospective

Sprint Two: 30 October to 1 November 2026 (3 days, last sprint). Team 5: Gagan, Varun, Tasya, Dikshith.
Goal: finish the admission cycle (choices, allotment, publication, result, seat decision) on the new design, prove the non-functional requirements and close the Sprint One gaps.

## What was delivered (merged into `main`)

| Pull request | What | Owner |
|---|---|---|
| #60 | Sprint Two plan, issue cards and final product mockup | Gagan |
| #63 | Shared contracts: six new tables with database rules, service names, error codes, journey contract, contract tests | Gagan |
| #61 | Audit `commit=False` so other modules can audit inside their own transaction | Tasya |
| #62 | Design system: shared shell, components and styles | Varun |
| #66 | Publish results service | Dikshith |
| #67, #68 | Choices: add, remove, reorder, lock (service, API and page) | Varun |
| #70 | Allotment engine, run service with lock and rollback, consistency report and script, administrator console | Gagan |
| #69 | Submit needs exam details (D2-02); application page on the new design; journey step | Gagan |
| #71 | Fictional demo dataset generator (300 and more candidates) | Tasya |
| #74 | Eligibility rules admin page | Tasya |
| #72 | Profile integrity and date of birth at registration (D-05) | Varun |
| #73 | CSRF protection on every state-changing request (D-03) | Dikshith |
| #75 | Publication card in the allotment console | Dikshith |
| #76 | Candidate journey dashboard (seven steps) | Varun |
| #77 | Candidate result page, allotment letter and one-time seat decision (ADM-F-018, ADM-F-019) | Dikshith |
| #78 | Administrator candidate list and response-time evidence (TC-026) | Tasya |
| #79 | Dashboard shows the real approved-document count (DEF-012); Varun's evidence and retrospective | Varun |
| #80 | Allotment timing script, seat-consistency evidence, SAD 1.3, deviations, defect log, this review | Gagan |
| #58, #64, #65 | Sprint One evidence | Tasya |

## Numbers

- Full suite on the final combined code (all pull requests above): **820 passed, 0 failed** (2 November 2026, Python 3.12.10).
- Allotment: Test Plan Appendix B oracle passes unchanged; 300 candidates median 0.967 s, 600 candidates median 1.589 s (limit 60 s); seat counts consistent after every run.
- Response time: tested candidate pages averaged 3 to 16 ms (target 2 s).
- Defects: 13 logged in `docs/DEFECT_LOG.md`; no Critical or High open; one Medium deferred (DEF-013, admin record correction).
- Deviations: `docs/DEVIATIONS.md`; all six Sprint One gaps and all four Day 3 open items closed; D-03 and D-05 done; D-23 is the one known gap.

## The whole cycle works end to end

Every step of the cycle runs on `main` through real routes, logins and CSRF tokens, covered in three automated tests: `tests/integration/test_demo_flow.py` (register, exam details, draft, submit, documents, review, resubmit, eligibility, catalogue), its TC-030 test (admin configuration through choices and allotment), and Dikshith's `tests/allotment/test_result_decision_flow.py` (the Appendix B candidates through run, publication, result, accept and reject, with seat counts unchanged). One continuous run from registration to decision is to be shown in the demo video (Dikshith).

## Retrospective: three lines from each person

Each person writes their own lines: what went well, what did not, what we would change.

**Gagan**
- Went well: contracts and database rules agreed in the first hours let four people build in parallel without breaking each other; the oracle and the database checks caught real mistakes before merge.
- Did not go well: some pull requests sat waiting for others and then conflicted with `main`; the result page arrived last, so the full cycle could only be tested at the end.
- Change next time: merge `main` into every branch each morning and build the end-to-end path first, with thin versions of each step, before polishing any one step.

**Varun**
- **What went well:** I delivered the shared UI integration, Choices functionality, Profile Integrity work, and seven-step Candidate Dashboard, and the available cross-module providers and automated regression tests are now integrated and passing.
- **What didn't go well:** Dependency timing and merge delays left provider contracts and evidence coordination late; Python 3.12 was unavailable locally, and responsive, keyboard-only and contrast validation still require manual verification.
- **What we'd change:** I would agree API/service contracts earlier, run cross-module integration tests sooner, coordinate ownership checkpoints more explicitly, and reserve dedicated time for Python 3.12 and accessibility validation.

**Tasya**
- (to be written by Tasya)

**Dikshith**
- (to be written by Dikshith)
