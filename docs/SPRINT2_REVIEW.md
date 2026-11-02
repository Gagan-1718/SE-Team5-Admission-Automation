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
| #58, #64, #65 | Sprint One evidence | Tasya |

## Numbers

- Full suite on `main` after #72 and #73: see `docs/evidence/gagan.md` and the CI run on the final merge.
- Allotment: Test Plan Appendix B oracle passes unchanged; 300 candidates median 0.967 s, 600 candidates median 1.589 s (limit 60 s); seat counts consistent after every run.
- Defects: see `docs/DEFECT_LOG.md` (severity and disposition for each).
- Deviations: `docs/DEVIATIONS.md`; all six Sprint One gaps closed; D-03 and D-05 done.

## Not finished at the time of writing (1 November)

See `docs/DEVIATIONS.md` section 7: candidate result page and seat decision (Dikshith), administrator candidate list and response-time measurement (Tasya), candidate journey dashboard pull request (Varun). Update this section before the `v1.0` tag.

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
