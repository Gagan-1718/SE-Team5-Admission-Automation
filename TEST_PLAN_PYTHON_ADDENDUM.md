# Python test environment and schedule update

Effective 19 October 2026. Apply this addendum to the existing TestPlan_Team5_Admission_Automation.pdf. Requirement IDs, TC-001 through TC-030, expected business outcomes and the allotment oracle are unchanged. The existing SRS remains authoritative.

## Section 6 environment

Use Python 3.12, Flask, SQLAlchemy and SQLite. Use pytest and Flask's test client for unit/integration and API permission tests; browser checks or Playwright for end-to-end flows; existing Postman/JMeter checks where useful. Replace the illustrative JUnit/PyTest/Jest selection with pytest. Test against isolated temporary SQLite files, not a developer's working records. Enable foreign keys on every connection. Use fictional exam records and documents.

Keep HTTPS/TLS verification, salted password hashing checks, server-side role/ownership tests, logout invalidation, CSRF protection, safe upload validation and read-only audit access. A local Flask development server does not demonstrate an HTTPS acceptance environment. No test is marked passed until it is executed and evidence is recorded.

## Section 7 revised proposed schedule

19 Oct: agree environment, schema and seed data; baseline the Python design. 20–22 Oct: test each merged Sprint One feature and the connected workflow. 23 Oct: Sprint One demonstration and regression. 26–29 Oct: choice/allotment/result integration, correctness, concurrency, performance and usability tests. 30 Oct: final planned regression and sprint review. These replace stale proposed October 6–14 start milestones; final submission date remains to be confirmed.

## Database-specific verification

Test duplicate simultaneous submission and unique reference generation, foreign-key enforcement, two competing allotment requests, rollback after a deliberate mid-run failure, rejection of a second completed allotment run, capacity bounds and once-only acceptance/rejection. Allotment must acquire a SQLite write transaction before checking completion and changing seats; result, seat counts, completion marker and audit entry commit together. Confirm lock/busy handling returns a clear failure and leaves no partial result. SQLite serializes writers; measure the actual response-time and workload criteria rather than assuming equivalence to MySQL. Run the existing hand-computed oracle unchanged.

SQLite has no per-user table grants. Verify audit UPDATE/DELETE are rejected by database triggers and no UI/API mutation path exists; INSERT and administrator SELECT remain possible. Database file protection is a deployment concern, not a guarantee against an operator with filesystem access.
