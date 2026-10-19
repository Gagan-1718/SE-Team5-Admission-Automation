# Software Architecture and Design Specification

Python revision 1.2 — 19 October 2026. This text revision supersedes the previous Java/MySQL technology choices. Functional requirements and API contracts are retained. Original UML figures remain in the source SAD; they describe the same logical modules and flows.

Software Architecture and Design Specification

Project: Admission Management Platform (Automated Engineering Admission & Counselling Management Platform for KCET and COMEDK)

Version: 1.2

Authors: Team 5 - Varun M L, Gagandeep N, Dikshith Varma M N, Tasya Shetty

Date: 19-10-2026

Status: Draft

## Revision History

| Version | Date | Author | Change Summary |
| --- | --- | --- | --- |
| 1.0 | 03-10-2026 | Team 5 | Initial draft of the SAD, derived from the SRS (Team 5). |
| 1.2 | 19-10-2026 | Team 5 | Adopt Python/Flask/SQLite and pytest; preserve requirement IDs and API contract; specify SQLite transaction and audit safeguards. |

## 1. Introduction

### 1.1 Purpose

This document specifies the architecture and design of the Admission Management Platform, a web-based system that supports a KCET/COMEDK-style engineering admission and seat-counselling workflow. It is derived entirely from the Software Requirements Specification (SRS) and explains how the SRS requirements are realised by components, interactions, interfaces and security mechanisms. It guides the implementation and testing of the system by the four-member project team.

### 1.2 Scope

In scope : Candidates can register, log in, manage their profile and exam details, save and submit an application, upload documents, check eligibility, browse the college/branch catalogue, fill, reorder and lock choices, view their allotment result and accept or reject the allotted seat. The Administrator can manage candidate records, verify documents, manage colleges, branches, category-wise seat capacity and eligibility rules, run seat allotment, publish results, use a consolidated dashboard and review the audit log. A single allotment cycle is implemented.

Out of scope : The following are explicitly excluded by the SRS and therefore have no place in this architecture: integration with real KEA/COMEDK systems or APIs, OCR or AI-based document verification, Aadhaar or biometric authentication, offline/kiosk modes, payment functionality (real or simulated), real SMS gateways, mandatory external e-mail services, in-app notifications, multiple counselling rounds, medical/dental admissions, post-admission management, and AI-based prediction, recommendation or graph analytics. All exam data, ranks, categories and eligibility rules are mock/seeded data. As a consequence, the system has no external system interfaces. Conflicts between the broad admission-platform features and these SRS constraints are recorded in section 3.11.

### 1.3 Audience

The student project team (developers and testers), the project guide/faculty evaluator, and reviewers assessing the completeness and testability of the design.

### 1.4 Definitions

| Term | Definition |
| --- | --- |
| Candidate | A prospective engineering student who registers on the platform. |
| Administrator | The single platform-operator role (verification, catalogue and seat-matrix management, allotment, publication, audit review). |
| Application | A candidate's formal request for admission, identified by a unique reference number. |
| Eligibility | Qualification status (Eligible, Not Eligible, Pending Verification) determined against configured, seeded rules. |
| Choice | A candidate-selected college-branch combination, ranked by preference. |
| Seat Matrix | Configured record of total, filled and available seats per college, branch and category. |
| Allotment Run | One execution of the allotment engine over the candidate pool and seat matrix. |
| Not Allocated | Outcome when none of a candidate's locked preferences can be satisfied. |
| RBAC | Role-Based Access Control. |
| NFR / RTM | Non-Functional Requirement / Requirements Traceability Matrix. |
| Assumption (A-xx) | A design assumption or choice made by the team where the SRS is silent. Listed in section 3.10. Assumptions are not SRS requirements. |

## 2. Document Overview

### 2.1 How to use this document

Section 3 describes the architecture (goals, component diagram and descriptions, pattern, technology, risks, traceability, security). Section 4 describes the design (sequence diagrams, API design, error handling/logging/monitoring, UX, open issues). Section 5 contains appendices.

Conventions. Requirement IDs (ADM-F-xxx, ADM-NFR-xxx, SEC-F-xxx) are copied unchanged from the SRS. Anything marked with an assumption ID (A-xx) is a design assumption made by the team because the SRS does not specify it (see section 3.10); it must not be read as an SRS requirement. Conflicts and inconsistencies are listed in section 3.11.

### 2.2 Related Documents

SRS - Automated Engineering Admission & Counselling Management Platform for KCET and COMEDK (Team 5): single source of truth for scope, requirements, roles, constraints and NFRs.

STP (Software Test Plan) and Python test environment addendum; test cases TC-001 to TC-030 are already referenced in the SRS.

RTM - SRS section 8 maps requirements to modules and test cases; section 3.8 of this SAD extends it to design elements.

### 2.3 Scope Priority

When sources conflict, the higher-priority source wins. An explicit SRS constraint is never silently overridden; every conflict is recorded in section 3.11 and every assumption in section 3.10.

| Priority | Source | Examples |
| --- | --- | --- |
| 1 | Explicit implementation requirements and constraints in the SRS | SRS 2.5 Constraints, 3.3 Software Interfaces, 3.4 Communications, Assumptions section (mock/seeded data, no payment, no external interfaces, manual document verification, single allotment cycle). |
| 2 | Explicit SRS scope and project constraints | SRS 1.2 Scope and out-of-scope list, 2.1 Product Perspective, 2.4 Operating Environment. |
| 3 | Functional and non-functional requirements | ADM-F-001 to ADM-F-020, ADM-NFR-001 to ADM-NFR-005, SEC-F-001 to SEC-F-005. |
| 4 | Other SRS design and interface information | SRS 3.1 user interfaces, section 7 use-case diagrams, glossary, RTM module names. |
| 5 | Clearly labelled design assumptions | Section 3.10 (A-01 to A-22). |

## 3. Architecture

### 3.1 Goals & Constraints

Goals :

Correct rank-, preference- and seat-based allotment (ADM-F-015, ADM-F-016).

Seat counts consistent with allotment records, never above capacity (ADM-NFR-003).

Candidate-facing pages respond within 2 seconds under normal load (ADM-NFR-001).

Allotment run for a few hundred candidates in reasonable time (ADM-NFR-002).

First-time candidates can submit an application without help (ADM-NFR-004).

Catalogue, seat-matrix and eligibility-rule data configurable, not hard-coded (ADM-NFR-005).

Authentication, RBAC, salted hashing, encrypted transport, audit log (SEC-F-001 to SEC-F-005).

Constraints :

Four-member team, single academic semester (SRS 2.5).

Mock/seeded exam and eligibility data; no real KEA/COMEDK integration (SRS 2.5, 3.3).

No payment, SMS or mandatory e-mail interfaces; no OCR (SRS 1.2, 3.3).

Small-to-moderate dataset (tens to a few hundred candidates); single allotment cycle; single Administrator role.

Browser-based client; all client-server communication over HTTPS (SRS 3.4).

### 3.2 Stakeholders & Concerns

| Stakeholder | Concerns |
| --- | --- |
| Candidates | Easy-to-follow workflow, privacy of personal data, clear document and result status, fair and correct allotment. |
| Administrator | Efficient document verification, configurable catalogue/seat data, reliable allotment, audit trail. |
| Developers / testers | Modularity, testability of the allotment algorithm, maintainability within one semester. |
| Faculty evaluator | Completeness, traceability to the SRS, correctness of the allotment engine. |

### 3.3 Component (UML) Diagram

Figure 1 shows the major components. The system is a single web application organised in layers. There are no external systems because the SRS excludes KEA/COMEDK, payment gateway, SMS/e-mail gateway and OCR/AI integrations; mock/seeded exam data is represented inside the Relational Database instead.

Figure 1: Component diagram. Modules inside the Application Layer reach data only through the Data Access Layer; uploaded files are kept in the Document File Store.

### 3.4 Component Descriptions

Every component shown in Figure 1 is described below.

| Component | Purpose | Main responsibilities | Interactions / dependencies |
| --- | --- | --- | --- |
| Candidate Web Interface | Browser UI for candidates. | Registration/login, profile and exam details, application form, document upload, eligibility status, catalogue, choice filling/locking, allotment result and seat decision (SRS 3.1). | Calls REST APIs through the Security Layer over HTTPS. |
| Administrator Web Interface | Browser UI for the Administrator. | Candidate management, document verification, college/branch/seat-matrix and eligibility-rule management, allotment execution, result publication, dashboard, audit log view. | Calls REST APIs through the Security Layer over HTTPS. |
| Security Layer | Gatekeeper for every request. | Enforces HTTPS, requires authentication for all functions except register/login (SEC-F-001), enforces RBAC (SEC-F-002), manages sessions. | Sits between both interfaces and all modules; asks Account Module to verify credentials. |
| Account Module | Candidate identity and credentials. | Registration (ADM-F-001), login/logout (ADM-F-002), profile and exam details (ADM-F-003), salted password hashing (SEC-F-003), role lookup. | Uses Data Access Layer (incl. seeded exam records); used by Security Layer, Application, Eligibility, Allotment, Admin modules. |
| Application Module | Admission application lifecycle. | Save draft, edit, submit with unique reference number (ADM-F-004, ADM-F-005). | Depends on Account Module for candidate data. |
| Document Module | Supporting-document handling. | Upload with type/size validation (ADM-F-006), admin approve/reject with reason (ADM-F-007), status view and resubmission (ADM-F-008). | Stores files in Document File Store, metadata in database; writes Audit Module entries for admin reviews; its statuses feed Eligibility Module. |
| Eligibility Module | Eligibility evaluation. | Evaluate exam details and category against configured rules; return Eligible / Not Eligible / Pending Verification with reason (ADM-F-009); rules editable by admin (ADM-NFR-005). | Reads exam details (Account), document statuses (Document), rules (database); result is used by Choice and Allotment modules. |
| Catalogue Module | Colleges, branches and seat matrix. | Candidate catalogue view with filter (ADM-F-010); admin add/edit/configure colleges, branches, category-wise capacity; seat availability updated after allotment (ADM-F-011). | Read by Choice and Allotment modules; admin changes logged via Audit Module. |
| Choice Module | Preference list management. | Add/remove/preview choices without duplicates (ADM-F-012), reorder (ADM-F-013), lock list (ADM-F-014). | Requires Eligible status (Eligibility) and catalogue data (Catalogue); locked lists feed Allotment Module. |
| Allotment Module | Seat allotment engine. | Run allotment in ascending rank order, first satisfiable locked preference, immediate seat reduction (ADM-F-015); mark Not Allocated (ADM-F-016); keep seat counts consistent (ADM-NFR-003). | Reads rank/category (Account), eligibility, locked choices, seat matrix; writes allotment records; logs the run via Audit Module. |
| Result Module | Result publication and seat decision. | Publish results (ADM-F-017), candidate result view (ADM-F-018), accept or reject/withdraw exactly once (ADM-F-019). | Depends on Allotment Module records; publication logged via Audit Module. |
| Admin Module | Administrative oversight. | Consolidated dashboard of candidates, application statuses and verification queues (ADM-F-020); candidate record management; audit log viewing. | Reads Account, Application, Document data; reads Audit Module log; changes logged via Audit Module. |
| Audit Module | Traceability of privileged actions. | Write append-only entries with actor, timestamp and action type (SEC-F-005); read-only retrieval for the Administrator. | Called by Document, Catalogue, Allotment, Result and Admin modules; stores entries via Data Access Layer. |
| Data Access Layer | Single point of database access. | Repositories for each entity; transaction handling (used by the allotment run). | Used by all modules; talks to Relational Database. |
| Relational Database | Persistent data store. | Candidates, applications, documents (metadata), colleges, branches, seat matrix, choices, allotment records, eligibility rules, seeded exam data, audit log. | Accessed only through Data Access Layer. |
| Document File Store | Storage for uploaded files. | Holds uploaded PDF/JPEG/PNG files (A-04). | Written/read by Document Module only. |

### 3.5 Chosen Architecture Pattern and Rationale

Pattern: layered modular monolith (presentation, application, data), with one module per SRS functional area. This matches the module names in the SRS traceability matrix (Account, Application, Document, Eligibility, Catalogue, Choice, Allotment, Result, Admin, Audit).

Why it fits: (1) one deployable application is realistic for a four-member team and one semester; (2) the dataset is small and there are no external systems, so distribution gives no benefit; (3) the allotment run must update seat counts consistently, which is simplest with one database and one transaction (ADM-NFR-003); (4) separate modules keep catalogue, rules and seat data configurable and testable (ADM-NFR-005).

Rejected alternatives: microservices and event-driven designs add network, deployment and consistency complexity with no SRS need; a separate document database is unnecessary because the data is relational.

The assumptions behind this choice (A-01 architecture, A-02 and A-03 technology, A-07 transactional allotment) are listed in section 3.10.

### 3.6 Technology Stack & Data Stores

The SRS does not mandate any programming language, framework or database (SRS 3.3, Assumptions). Every technology below is therefore a design/implementation choice unless the Basis column says it is an SRS requirement.

| Technology | Used for | Basis |
| --- | --- | --- |
| Modular monolith | Overall architecture: one deployable application with one module per SRS functional area. | Design choice (A-01). |
| Web application (Flask Jinja templates, HTML5, CSS/Bootstrap and minimal JavaScript) | Candidate and Administrator interfaces. | A web-based, browser-accessed system is an SRS requirement (1.1, 2.4, 3.1); the client technologies are a design choice (A-02). |
| Python 3.12, Flask and SQLAlchemy | Python application services, Flask routes and SQLAlchemy data access. | Design choice (A-02); the SRS leaves the framework to the team (3.3). |
| Flask-Login, Flask-Session and Flask-WTF with server-side role and ownership checks | Authentication, RBAC, sessions in the Security Layer. | Design choice (A-02) realising SEC-F-001 and SEC-F-002, which are SRS requirements. |
| SQLite | Relational Database. | Design choice (A-03); the SRS allows a relational or document database (3.3). |
| BCrypt | Salted password hashing in the Account Module. | Design choice (A-02); SEC-F-003 requires a salted cryptographic hash but names no algorithm. |
| REST + JSON | Interface between the web client and the modules. | Design choice (A-20). |
| HTTPS/TLS | All client-server communication. | SRS requirement (3.4, SEC-F-004); TLS version and certificate set-up are an assumption (A-16). |
| pytest | Unit tests, including the allotment algorithm. | Design choice (A-02). |
| Postman | API testing. | Design choice (A-02). |
| JMeter | Response-time and allotment-run timing checks. | Design choice (A-02); the SRS asks only for informal timing or a lightweight load-testing tool (ADM-NFR-001, ADM-NFR-002). |
| Python / Matplotlib (where applicable) | Drawing the diagrams in this document. | Documentation tool choice (A-02). |
| draw.io / PlantUML (where applicable) | Editing or redrawing the diagrams. | Documentation tool choice (A-02). |
| Server directory | Document File Store. | Design choice (A-04). |

Data stores. One relational database (contents listed in section 3.4) plus the Document File Store for uploaded files (A-04).

### 3.7 Risks & Mitigations

| Risk | Mitigation | SRS ref. |
| --- | --- | --- |
| Allotment gives wrong results | Unit tests on a seeded dataset compared with a hand-computed result; deterministic processing order. | ADM-F-015, TC-015 |
| Seat counts inconsistent, or run fails midway | Single transaction (A-07) with rollback; database constraint allotted <= capacity; post-run consistency check. | ADM-NFR-003 |
| Candidate reaches admin functions | RBAC enforced on the server for every admin endpoint, not only in the UI. | SEC-F-002 |
| Exposure of personal data | HTTPS only; salted password hashes; candidates can read only their own records (A-14); no personal data in logs. | SEC-F-003, SEC-F-004 |
| Unsafe or invalid file uploads | Type (PDF/JPEG/PNG) and size validation; files stored outside web root with generated names (A-04). | ADM-F-006 |
| Audit entries altered | No edit/delete path in the application; audit INSERT/SELECT access in application code and SQLite triggers rejecting UPDATE/DELETE (A-17). | SEC-F-005 |
| Slow pages or slow allotment | Indexed lookups (rank, seat matrix); process candidates in memory within the transaction; time both during demos. | ADM-NFR-001, ADM-NFR-002 |

### 3.8 Traceability to Requirements

IDs below are exactly those in the SRS. Section references point to this SAD (SD = sequence diagram in 4.2; API = 4.3).

| Req. ID | Summary | SAD component(s) | Design element |
| --- | --- | --- | --- |
| ADM-F-001 | Candidate registration | Account Module | SD-1; API: POST /auth/register |
| ADM-F-002 | Candidate login/logout | Account Module, Security Layer | SD-1; API: POST /auth/login, /auth/logout |
| ADM-F-003 | Profile and exam-detail management | Account Module | API: PUT /candidates/me/profile, /exam-details; A-09 |
| ADM-F-004 | Save application as draft | Application Module | API: POST /applications, PUT /applications/{id} |
| ADM-F-005 | Edit, submit; reference number | Application Module | API: POST /applications/{id}/submit |
| ADM-F-006 | Document upload and validation | Document Module, Document File Store | SD-2; API: POST /documents |
| ADM-F-007 | Document approve/reject | Document Module, Administrator Web Interface | SD-2; API: PUT /admin/documents/{id}/review |
| ADM-F-008 | Document status and resubmission | Document Module | SD-2; API: GET /documents, PUT /documents/{id} |
| ADM-F-009 | Eligibility and reason display | Eligibility Module | SD-2; API: GET /candidates/me/eligibility; A-08 |
| ADM-F-010 | College/branch catalogue view | Catalogue Module | API: GET /colleges |
| ADM-F-011 | Admin college/branch/seat management | Catalogue Module | API: /admin/colleges, /admin/seat-matrix |
| ADM-F-012 | Choice add/remove/preview | Choice Module | API: GET/POST /choices, DELETE /choices/{id} |
| ADM-F-013 | Choice reordering | Choice Module | API: PUT /choices/order |
| ADM-F-014 | Choice locking | Choice Module | API: POST /choices/lock |
| ADM-F-015 | Allotment engine | Allotment Module | SD-3; 4.1 algorithm; API: POST /admin/allotment/run |
| ADM-F-016 | Not Allocated determination | Allotment Module | SD-3 (alt branch); 4.1 algorithm |
| ADM-F-017 | Result publication | Result Module | SD-3; API: POST /admin/allotment/runs/{runId}/publish |
| ADM-F-018 | Result viewing | Result Module | SD-3; API: GET /allotment/result |
| ADM-F-019 | Seat accept/reject (once) | Result Module | SD-3; API: POST /allotment/decision |
| ADM-F-020 | Admin dashboard | Admin Module | API: GET /admin/dashboard, /admin/candidates |
| ADM-NFR-001 | Response time <= 2 s | All modules; Data Access Layer | Indexed queries; response-time logging (4.4) |
| ADM-NFR-002 | Allotment run scalability | Allotment Module | In-memory processing in one transaction; run duration logged |
| ADM-NFR-003 | Seat-count consistency | Allotment Module, Relational Database | A-07; capacity constraint; consistency check (4.4) |
| ADM-NFR-004 | Candidate usability | Web Interfaces | Section 4.5 |
| ADM-NFR-005 | Configurable data-driven design | Catalogue Module, Eligibility Module | A-06; admin screens for catalogue, seats, rules |
| SEC-F-001 | Mandatory authentication | Security Layer, Account Module | Section 3.9 |
| SEC-F-002 | Role-based access control | Security Layer | Section 3.9 (access matrix) |
| SEC-F-003 | Salted password hashing | Account Module | BCrypt; Section 3.9 |
| SEC-F-004 | Encrypted data in transit | Security Layer / server configuration | HTTPS only; Section 3.9 |
| SEC-F-005 | Audit logging of privileged actions | Audit Module | Section 3.9; 4.4 |

### 3.9 Security Architecture

The design covers only the security requirements stated in the SRS (objectives: protect candidate data, restrict privileged operations to authorised administrators, preserve integrity and traceability of admission actions).

| SRS req. | Design mechanism |
| --- | --- |
| SEC-F-001 | Security Layer rejects any request without a valid session (redirect to login / 401). Only register and login are public. |
| SEC-F-002 | Server-side role check on every endpoint (see access matrix). Candidate accounts get 403 on admin functions. |
| SEC-F-003 | Account Module stores only BCrypt (salted) hashes; passwords are never stored or logged. |
| SEC-F-004 | All traffic over HTTPS/TLS, including credentials and personal data. |
| SEC-F-005 | Audit Module writes actor, timestamp and action type for every privileged admin action; append-only, with no edit path in the UI. |

Access matrix.

| Function area | Public | Candidate | Administrator |
| --- | --- | --- | --- |
| Register, login | Yes | - | - |
| Own profile, application, documents, eligibility, choices, result, seat decision | - | Yes (own records only, A-14) | - |
| Catalogue view | - | Yes | Yes |
| Document verification, catalogue/seat-matrix/rule management, allotment run, result publication, dashboard, audit log | - | Denied (403) | Yes |

Integrity of admission data. Candidates cannot set their own rank or category (A-09). Seat availability, allotment results and publication can be changed only through Administrator-only functions, all audited. The allotment run is transactional, so results always match seat counts (ADM-NFR-003).

STRIDE summary (lightweight). Spoofing - authentication and salted hashes (SEC-F-001, SEC-F-003). Tampering - HTTPS (SEC-F-004), admin-only seat/allotment changes (SEC-F-002), transactional allotment. Repudiation - audit log (SEC-F-005). Information disclosure - HTTPS, RBAC, own-records-only access (A-14), no passwords or personal data in logs. Denial of service - not required by the SRS; no dedicated mitigation in this prototype. Elevation of privilege - server-side RBAC on every admin endpoint (SEC-F-002).

Not part of this design. The SRS does not require MFA, encryption at rest or OTP verification, so they are not designed here; MFA for the Administrator and encryption at rest are listed as possible enhancements in section 4.6.

### 3.10 Assumptions

Assumptions are design choices made by the team where the SRS is silent. They are not SRS requirements. All assumptions used anywhere in this document are listed here.

| Assumption ID | Assumption | Why It Is Needed | Impact on Design |
| --- | --- | --- | --- |
| A-01 | The system is a layered modular monolith deployed as one web application. | The SRS names no architecture; the team has four members and one semester (SRS 2.5). | Section 3.5, Figure 1; no distributed components. |
| A-02 | Python 3.12, Flask and SQLAlchemy, Flask-Login, Flask-Session and Flask-WTF with server-side role and ownership checks, BCrypt, HTML5/CSS/Bootstrap/JavaScript client, pytest, Postman, JMeter, Python/Matplotlib and draw.io/PlantUML are used. | The SRS leaves framework and tooling to the team (3.3, Assumptions). | Section 3.6; component implementation and testing approach. |
| A-03 | SQLite is the database. | The SRS allows a relational or document database without choosing one. | Relational Database component; transactions and constraints used for ADM-NFR-003. |
| A-04 | Uploaded files are stored on the server file system outside the public web root with generated names; metadata is stored in the database. | ADM-F-006 requires upload but not where files are kept. | Document File Store component; Document Module. |
| A-05 | Login uses a server-side session; the single Administrator account is created by a seed script (no public admin registration). | The SRS requires authentication but not the session mechanism or how the Administrator account is created. | Security Layer; Account Module; seed data. |
| A-06 | Eligibility rules, the required-document list, colleges, branches and seat capacities are database rows editable through admin screens. | ADM-NFR-005 requires configurable data; the SRS does not define the rule content or which documents are required. | Eligibility and Catalogue modules; admin endpoints in 4.3.4. |
| A-07 | The allotment run executes in one SQLite BEGIN IMMEDIATE transaction. After acquiring the write lock, check the persisted single-cycle completion flag before allocating; commit results, seat counts, completion flag and audit together. Roll back on failure and handle database-busy errors without partial changes. | ADM-NFR-003 requires seat counts always consistent with allotment records. | Allotment Module; a failed run leaves no partial allocations (SD-3). |
| A-08 | Eligibility is Pending Verification while required documents are not all Approved, Not Eligible if a rule fails, otherwise Eligible. | ADM-F-009 says document verification may affect final status but does not say how. | Eligibility Module logic; SD-2. |
| A-09 | A candidate's rank and category are taken from the seeded exam record matching the details entered; entries with no matching record are rejected. | ADM-F-003 and TC-003 do not say whether candidate-entered values are trusted (see C-10). | Account Module; PUT /candidates/me/exam-details (422 error). |
| A-10 | Ranks are compared as stored (KCET and COMEDK in one ordered run); ties are broken by application reference number. | ADM-F-015 says "ascending order of rank" but not how ties or two exam types are handled. | Allotment algorithm step 2 (4.1). |
| A-11 | Only the seat-matrix row for the candidate's own category is used; there is no cross-category fallback. | ADM-F-015 mentions category rules but defines none (see C-11). | Allotment algorithm step 3 (4.1). |
| A-12 | A rejected or withdrawn seat is not released and there is no re-allotment. | ADM-F-019 records the decision only; the SRS implements a single cycle. | Result Module; no seat-release logic. |
| A-13 | Only one completed allotment run exists per cycle; a failed (rolled-back) run may be repeated. | The SRS says "single allotment cycle" but not whether Run Allotment may repeat (see C-12). | POST /admin/allotment/run returns 409 after a completed run. |
| A-14 | Candidates can access only their own records. | SEC-F-002 only requires restricting admin functions; protecting personal data is objective 1 (SRS 5.1.1). | Security Layer ownership check (403); access matrix in 3.9. |
| A-15 | The Security Layer is a cross-cutting component that enforces SEC-F-001, SEC-F-002 and SEC-F-004. | The SRS RTM lists these under the Account Module and "Cross-cutting". | Security Layer in Figure 1 and 3.4. |
| A-16 | HTTPS uses a TLS version and certificate supported by the chosen server; a locally generated certificate is acceptable for the lab demonstration. | SEC-F-004 requires HTTPS/TLS but names no TLS version. | Server configuration only; no impact on modules. |
| A-17 | The audit log is append-only: no edit/delete path in the application and SQLite triggers rejecting audit UPDATE/DELETE, while allowing INSERT and SELECT; SQLite has no database user grants. Entries hold actor, timestamp, action type, target record id and outcome. Audited actions: document review, candidate record changes, catalogue/seat-matrix/rule changes, allotment run, result publication. | SEC-F-005 requires actor, timestamp and action type and that entries are not editable in the standard UI, but does not list every audited action. | Audit Module; audit_log table. |
| A-18 | Administrator "manage candidate records" (ADM-F-020) means view and correct record fields, with each change audited. | ADM-F-020 does not define "manage". | PUT /admin/candidates/{id}; Admin Module. |
| A-19 | The maximum upload size is a configuration value to be agreed by the team. | ADM-F-006 requires a size limit but gives no value. | Document Module validation reads the configured limit. |
| A-20 | The REST API uses base path /api/v1, JSON bodies, session cookie and the error body {status, error, message}. | The SRS gives no API conventions. | Section 4.3. |
| A-21 | Monitoring is lightweight: logged response times and run duration, a post-run consistency check and a health-check endpoint; the application log excludes passwords and personal details. | The SRS gives no logging or monitoring requirements beyond audit logging and measurable NFRs. | Section 4.4. |
| A-22 | The candidate UI uses a guided step tracker, confirmation prompts for irreversible actions and basic accessibility practices. | ADM-NFR-004 requires first-time usability without defining UI patterns; the SRS has no accessibility requirement. | Section 4.5; no extra modules. |

### 3.11 Conflicts / Inconsistencies

"Brief" means the instructions given to the team for producing this SAD. Rows C-01 to C-08 are conflicts between the brief and the SRS; the SRS prevails (section 2.3). Rows C-09 to C-13 are ambiguities inside the SRS itself.

| Conflict ID | Conflict / Inconsistency | Source 1 | Source 2 | Design Handling |
| --- | --- | --- | --- | --- |
| C-01 | KEA/COMEDK score and rank import / API expected, but the SRS excludes real integration and uses mock/seeded data. | Brief (external systems, score import) | SRS 1.2, 2.1, 2.5, 3.3 | SRS prevails. No external API designed; seeded exam data is held in the Relational Database; Figure 1 shows no external systems. |
| C-02 | Fee payment, receipts and a payment gateway expected, but the SRS excludes payment functionality, real or simulated. | Brief (payment, receipts) | SRS 1.2, 2.5, Assumptions | SRS prevails. No payment module, API or sequence step; the flow ends at the seat decision (ADM-F-019). |
| C-03 | OCR-assisted document checking expected, but the SRS requires manual administrator verification only. | Brief (OCR) | SRS 1.2, ADM-F-007, Assumptions | SRS prevails. Manual approve/reject only (SD-2); no OCR component. |
| C-04 | OTP verification and SMS/e-mail notifications expected, but SRS login is e-mail/mobile plus password and no external or in-app notification channel exists. | Brief (OTP, SMS/e-mail) | SRS ADM-F-001, ADM-F-002, 1.2, 3.3, 3.4 | SRS prevails. No OTP step (SD-1) and no notification component; candidates see status after logging in. |
| C-05 | Multiple counselling rounds, mock and final allotment, seat freeze/float, college reporting, grievance/helpdesk and MIS/analytics export expected, but the SRS defines a single allotment cycle with accept/reject only. | Brief (functions list) | SRS 1.2, 2.2, ADM-F-015 to ADM-F-019 | SRS prevails. None designed. Multiple rounds appear only as a possible future enhancement (4.6), as in the SRS. |
| C-06 | MFA, AES-256 at rest, TLS 1.2+ and immutable audit logs expected, but the SRS requires password authentication, HTTPS/TLS (no version), salted hashes and an audit log not editable through the standard UI. | Brief (security list) | SRS SEC-F-001 to SEC-F-005 | SRS prevails. Only SEC-F-001 to SEC-F-005 are designed. TLS details are A-16; audit log design is A-17. MFA and encryption at rest are not designed. |
| C-07 | Availability, data retention, accessibility (Kannada, screen reader, high contrast) and large-scale performance expected, but the SRS defines five NFRs for a small dataset and none of these. | Brief (NFR list) | SRS 2.5, 5 | SRS prevails. Only ADM-NFR-001 to ADM-NFR-005 are designed. Basic accessibility practice is A-22 and is not a requirement. |
| C-08 | Requirement IDs named in the brief (ADM-NF-001, PRJ-SR-001) do not exist in the SRS. | Brief (traceability IDs) | SRS 5, 5.1.2, 8 | SRS IDs (ADM-NFR-xxx, SEC-F-xxx) are used unchanged in section 3.8. |
| C-09 | The administrator use-case diagram shows "Verify Eligibility", but no functional requirement describes manual eligibility verification; ADM-F-009 is automatic. | SRS 7.2 | SRS ADM-F-009 | Eligibility is automatic; the Administrator sees status and can edit rules and documents. No manual override designed. Requires clarification from project stakeholders. |
| C-10 | ADM-F-003 says the candidate enters rank, category and score, but exam data is seeded and TC-003 stores values for a matching seeded record; it is unclear whether entered values are trusted. | SRS ADM-F-003 | SRS 1.2, TC-003 | Handled by A-09 (values come from the matching seeded record). Requires clarification from project stakeholders. |
| C-11 | ADM-F-015 allocates the first preference "that is eligible", but eligibility (ADM-F-009) is a candidate-level status; per-preference eligibility is undefined. | SRS ADM-F-015 | SRS ADM-F-009 | Candidate must be Eligible and the seat row matches the candidate's category (A-11). Requires clarification from project stakeholders. |
| C-12 | "Single allotment cycle" versus an Administrator "Run Allotment" action: whether a run can be repeated is not stated. | SRS 1.2, glossary | SRS ADM-F-015, ADM-F-017 | Handled by A-13. Requires clarification from project stakeholders. |
| C-13 | Seat availability updates "after each allotment run" (ADM-F-011) but "immediately after each allocation" (ADM-F-015). | SRS ADM-F-011 | SRS ADM-F-015 | Both satisfied: counts are reduced immediately inside the run transaction and become visible when it commits. No further action needed. |

4. Design

4.1 Design Overview

Every request follows one path: Web Interface -> HTTPS -> Security Layer (authentication, RBAC) -> Flask route handler -> module service -> Data Access Layer -> Relational Database. Each module owns its entities and exposes services to other modules only where Figure 1 and section 3.4 show a dependency.

Status values used across the design (from the SRS):

| Item | States | Rule |
| --- | --- | --- |
| Application | Draft -> Submitted | Submit only when mandatory fields are complete; reference number generated once (ADM-F-005). |
| Document | Pending Verification -> Approved / Rejected | Rejected requires a reason; resubmission resets to Pending Verification (ADM-F-007/008). |
| Eligibility | Eligible / Not Eligible / Pending Verification | Evaluated per ADM-F-009 and A-08. |
| Choice list | Open -> Locked | No add/remove/reorder after locking (ADM-F-014). |
| Allotment run | Completed -> Published | Candidates see results only after publication (ADM-F-017). One run per cycle (A-13). |
| Allotment result | Allocated / Not Allocated | Per candidate (ADM-F-016). |
| Seat decision | None -> Accepted / Rejected | Allowed exactly once (ADM-F-019). |

Allotment algorithm (ADM-F-015, ADM-F-016).

Start a SQLite BEGIN IMMEDIATE transaction; after obtaining the write lock, reject an already-completed cycle, then load eligible candidates with locked choice lists and the seat matrix.

Sort candidates by ascending rank (ties broken by application reference number - A-10).

For each candidate, walk the locked choices in saved order and pick the first one that has a free seat in the seat-matrix row for that college, branch and the candidate's category (A-11: only the candidate's own category row is used).

If found, save the allocation and reduce that seat availability immediately; otherwise save Not Allocated.

Write the audit entry and completion flag inside the transaction, then commit. On any error, roll back so no partial result remains.

4.2 UML Sequence Diagrams

Three project-specific flows are shown. In SD-2 and SD-3, requests pass through the Web Interface and Security Layer (authentication and RBAC) before reaching the module; this is omitted from the figures for readability.

SD-1: Candidate registration and login (ADM-F-001, ADM-F-002, SEC-F-001)

Figure 2: SD-1 Registration and login. Registration creates the account directly (no OTP step in the SRS).

SD-2: Document upload, verification, resubmission and eligibility (ADM-F-006 to ADM-F-009)

Figure 3: SD-2 Document upload, manual verification by the Administrator, resubmission and eligibility check.

SD-3: Allotment, publication, result view and seat decision (ADM-F-015 to ADM-F-019)

Figure 4: SD-3 Allotment run, result publication, candidate result view and one-time seat decision.

4.3 API Design

Conventions (A-20). Base path /api/v1 (omitted below); JSON over HTTPS; session cookie after login. Paths under /admin require the Administrator role. Errors use the body {status, error, message}. Common errors for protected endpoints: 401 not logged in, 403 wrong role or record not owned by the caller, 404 record not found; they are not repeated in every row.

4.3.1 Account Module

| Method and endpoint | Purpose | Request | Response | Specific errors |
| --- | --- | --- | --- | --- |
| POST /auth/register | Register candidate (ADM-F-001) | {name, email, mobile, dateOfBirth, password} | 201 {candidateId, message} | 400 invalid fields; 409 duplicate email/mobile |
| POST /auth/login | Log in (ADM-F-002) | {identifier (email or mobile), password} | 200 {role}; session started | 401 invalid credentials |
| POST /auth/logout | Log out | Session cookie | 204 | - |
| PUT /candidates/me/profile | Update contact details, address (ADM-F-003) | {contact details, address} | 200 updated profile | 400 invalid fields |
| PUT /candidates/me/exam-details | Enter exam details (ADM-F-003) | {examType, rank, category, score} | 200 {rank, category stored} | 422 no matching seeded record |

4.3.2 Application Module

| Method and endpoint | Purpose | Request | Response | Specific errors |
| --- | --- | --- | --- | --- |
| POST /applications | Create draft (ADM-F-004) | {application fields (partial allowed)} | 201 {applicationId, status: Draft} | 409 candidate already has an application |
| PUT /applications/{id} | Save or edit draft | {application fields} | 200 {status: Draft} | 409 already Submitted |
| GET /applications/me | Resume draft / view status | - | 200 {fields, status, referenceNumber?} | - |
| POST /applications/{id}/submit | Submit (ADM-F-005) | - | 200 {referenceNumber, status: Submitted} | 422 mandatory fields missing (field-level list); 409 already Submitted |

4.3.3 Document Module

| Method and endpoint | Purpose | Request | Response | Specific errors |
| --- | --- | --- | --- | --- |
| POST /documents | Upload document (ADM-F-006) | multipart {documentType, file} | 201 {documentId, status: Pending Verification} | 415 type not PDF/JPEG/PNG; 413 file too large |
| GET /documents | View own document statuses (ADM-F-008) | - | 200 [{documentId, type, status, rejectionReason?}] | - |
| PUT /documents/{id} | Resubmit rejected document (ADM-F-008) | multipart {file} | 200 {status: Pending Verification} | 409 document not Rejected; 415; 413 |
| GET /admin/documents?status=Pending | Verification queue (ADM-F-007, ADM-F-020) | Query: status | 200 list of documents | - |
| PUT /admin/documents/{id}/review | Approve or reject (ADM-F-007) | {decision: Approved\|Rejected, reason?} | 200 {status} | 422 reason missing when Rejected |

4.3.4 Eligibility and Catalogue Modules

| Method and endpoint | Purpose | Request | Response | Specific errors |
| --- | --- | --- | --- | --- |
| GET /candidates/me/eligibility | Evaluate eligibility (ADM-F-009) | - | 200 {status, reason} | 422 exam details not entered |
| POST/PUT /admin/eligibility-rules | Manage rules (ADM-NFR-005) | {rule parameters} | 201 / 200 {ruleId} | 400 invalid rule |
| GET /colleges?search= | Catalogue with seat availability (ADM-F-010) | Optional search term | 200 [{college, branches, seatsAvailable}] | - |
| POST/PUT /admin/colleges, /admin/colleges/{id}/branches | Add/edit colleges and branches (ADM-F-011) | {name, details} | 201 / 200 | 409 duplicate name |
| POST/PUT /admin/seat-matrix | Configure category-wise capacity (ADM-F-011) | {collegeId, branchId, category, capacity} | 200 {seatMatrixRow} | 422 invalid capacity |

4.3.5 Choice Module

| Method and endpoint | Purpose | Request | Response | Specific errors |
| --- | --- | --- | --- | --- |
| GET /choices | Preview choice list (ADM-F-012) | - | 200 [{choiceId, college, branch, priority}], locked flag | - |
| POST /choices | Add choice (ADM-F-012) | {collegeId, branchId} | 201 {choiceId, priority} | 403 candidate not Eligible; 409 duplicate choice; 409 list locked |
| DELETE /choices/{id} | Remove choice (ADM-F-012) | - | 204 | 409 list locked |
| PUT /choices/order | Reorder (ADM-F-013) | {orderedChoiceIds} | 200 new order | 409 list locked; 400 ids do not match list |
| POST /choices/lock | Lock list (ADM-F-014) | - | 200 {locked: true} | 409 already locked |

4.3.6 Allotment and Result Modules

| Method and endpoint | Purpose | Request | Response | Specific errors |
| --- | --- | --- | --- | --- |
| POST /admin/allotment/run | Run allotment (ADM-F-015, ADM-F-016) | - | 200 {runId, allocatedCount, notAllocatedCount, durationMs} | 409 run already completed (single cycle); 500 run failed and rolled back |
| POST /admin/allotment/runs/{runId}/publish | Publish results (ADM-F-017) | - | 200 {status: Published} | 409 run not completed or already published |
| GET /allotment/result | Candidate result (ADM-F-018) | - | 200 {college?, branch?, status: Allocated\|Not Allocated} | 404 results not published yet |
| POST /allotment/decision | Accept or reject/withdraw (ADM-F-019) | {decision: Accept\|Reject} | 200 {decisionStatus} | 409 decision already recorded; 422 result is Not Allocated |

4.3.7 Admin and Audit Modules

| Method and endpoint | Purpose | Request | Response | Specific errors |
| --- | --- | --- | --- | --- |
| GET /admin/dashboard | Counts, statuses, pending queues (ADM-F-020) | - | 200 {candidateCounts, statusCounts, pendingDocuments} | - |
| GET /admin/candidates, GET /admin/candidates/{id} | View candidate and application records (ADM-F-020) | Optional filters | 200 list / record | - |
| PUT /admin/candidates/{id} | Correct candidate record (A-18: scope of "manage") | {fields} | 200 updated record | 400 invalid fields |
| GET /admin/audit-logs | View audit log (SEC-F-005) | Optional filters | 200 [{actor, timestamp, actionType, target}] | - |

4.4 Error Handling, Logging & Monitoring

Error handling. Validation happens on the server for every request. Messages shown to users are clear but never reveal internal details or stack traces.

| Situation | System response | HTTP |
| --- | --- | --- |
| Invalid login | Generic "invalid credentials" message; access denied (TC-002). | 401 |
| Duplicate email/mobile at registration | Registration rejected with message (TC-001). | 409 |
| Invalid file type or oversized file | Upload rejected with explanatory message (TC-006). | 415 / 413 |
| Rejected document | Rejection reason stored and shown; candidate may resubmit (TC-007, TC-008). | - |
| Incomplete application submitted | Field-level errors; status stays Draft (TC-005). | 422 |
| Exam details match no seeded record | Details rejected with message (A-09). | 422 |
| Duplicate choice; modifying a locked list; choice when not Eligible | Request rejected with message (TC-012, TC-014). | 409 / 403 |
| Unauthenticated access | Redirect to login; no data returned (TC-021). | 401 |
| Candidate calls admin function | Denied with authorization error (TC-022); logged as a warning. | 403 |
| Invalid state (publish before run, second decision, results not yet published) | Request rejected with message; no data changed. | 409 / 404 |
| Allotment run failure | Transaction rolled back; Administrator sees an error; failure logged. | 500 |
| Unexpected server or database error | Generic error message; details only in the application log. | 500 |

Error cases involving OTP, OCR/document mismatch, score import, payment or external API failure do not apply, because the SRS excludes those features and external interfaces.

Logging.

Application log (A-21): timestamp, level, request id, user id and role, action, outcome. It never contains passwords, session identifiers, document contents or personal details such as e-mail, mobile number or date of birth; internal ids and the application reference number are used instead (SEC-F-003).

Audit log (SEC-F-005): actor identity, timestamp and action type, plus target record id (A-17). Entries are written for document approval/rejection, candidate record changes, college/branch/seat-matrix/eligibility-rule changes, allotment run and result publication. The log is append-only and read-only in the UI.

Monitoring (lightweight, A-21).

Response time of each request is logged to check the 2-second target (ADM-NFR-001).

Allotment run duration is logged to check the run-time target (ADM-NFR-002).

A consistency check (script or query) confirms allotted count does not exceed capacity for every college-branch-category after each run (ADM-NFR-003).

A health-check endpoint and counts of failed logins and 403 responses from the application log support demo-time monitoring.

4.5 UX Design

Responsive web interface (SRS 3.1): one Bootstrap-based layout that adapts to desktop and mobile browsers, with separate candidate and administrator views protected by role.

Guided candidate flow (A-22, supports ADM-NFR-004): the candidate dashboard shows a step tracker - Profile and exam details, Application, Documents, Eligibility, Choices, Allotment result, Seat decision - each showing its current status. Steps open in the dependency order given in the SRS (for example choices require Eligible status).

Clear feedback: field-level errors on the application form, visible rejection reasons on documents, duplicate-choice and locked-list messages, and an eligibility reason when the result is not Eligible.

Choice filling: catalogue with an optional search box, add/remove buttons, up/down reordering, and a Lock button with a confirmation prompt because locking cannot be undone.

Result and decision: results appear only after publication; Accept and Reject/Withdraw each ask for confirmation because the decision can be made only once.

Administrator workflow: dashboard with counts and the pending-verification queue; document review screen with Approve/Reject and a mandatory reason; college, branch, seat-matrix and rule editors; an allotment screen where Run and then Publish are enabled in that order; a read-only audit log table.

Basic accessibility (A-22, good practice rather than an SRS requirement): semantic HTML, labelled form fields, readable contrast and full keyboard operation.

| Screen (SRS 3.1) | User | Module(s) |
| --- | --- | --- |
| Registration / login | Candidate | Account |
| Profile and exam details | Candidate | Account |
| Application form | Candidate | Application |
| Document upload and status | Candidate | Document |
| Eligibility status | Candidate | Eligibility |
| College/branch catalogue; choice filling and locking | Candidate | Catalogue, Choice |
| Allotment result and seat decision | Candidate | Result |
| Candidate management and dashboard | Administrator | Admin, Account, Application |
| Document verification | Administrator | Document |
| College/branch/seat-matrix and rule management | Administrator | Catalogue, Eligibility |
| Allotment execution and result publication | Administrator | Allotment, Result |
| Audit log viewing | Administrator | Audit, Admin |

4.6 Open Issues & Next Steps

Open issues (SRS does not specify; each needs a team decision).

| # | Issue | Current design assumption (section 3.10) |
| --- | --- | --- |
| 1 | Content of eligibility rules (e.g. rank cut-offs, category rules). | Rules are admin-editable rows; the team seeds a sample rule set covering the three TC-009 cases. |
| 2 | Which documents are "required", and the maximum file size. | Required-document list is configurable data; file size limit is a configuration value (to be agreed). |
| 3 | Ordering of KCET and COMEDK candidates in one rank-ordered run, and rank ties. | Ranks are compared as stored; ties broken by application reference number. Seed data should avoid ambiguity. |
| 4 | Category/reservation matching beyond the seat-matrix category. | Only the candidate's own category row is used; no cross-category fallback. |
| 5 | Whether a rejected/withdrawn seat is released. | Not released; no re-allotment, because only one cycle is implemented. |
| 6 | Re-running allotment after a completed run. | Only one completed run per cycle; a failed run leaves no data and may be repeated. |

Next steps.

Agree the open issues above and prepare the seed data (exam records, rules, colleges, seat matrix, one Administrator account).

Implement modules in dependency order: Account, Application/Document, Catalogue/Eligibility, Choice, Allotment/Result, Admin/Audit.

Execute the existing STP cases TC-001 to TC-030 using the Python environment addendum and update RTM status values as development proceeds.

Possible future enhancements (not SRS requirements): multiple counselling rounds (noted in the SRS as a future possibility), MFA for the Administrator, encryption of stored data, and additional language and accessibility options.

5. Appendices

5.1 Glossary

Terms in section 1.4 apply. Additional terms:

| Term | Meaning |
| --- | --- |
| BCrypt | Password-hashing function that adds a random salt to each hash. |
| Modular monolith | One deployable application divided into clearly separated modules. |
| Transaction | A group of database changes that are all saved together or all undone. |
| Seeded data | Mock records loaded into the database for development and demonstration. |

5.2 References

Software Requirements Specification: Automated Engineering Admission & Counselling Management Platform for KCET and COMEDK (Team 5).

SAD template (Software Architecture and Design Specification).

ISO/IEC/IEEE 42010 - Architecture description.

OWASP Top 10 and OWASP Cheat Sheet Series (authentication, password storage, file upload).

Flask, SQLAlchemy, SQLite, Flask-Login, Flask-Session and Flask-WTF documentation.

5.3 Tools

Python/Matplotlib was used to draw the diagrams in this document; draw.io or PlantUML can be used to edit or redraw them. Implementation and test tools (Flask, authentication and CSRF extensions, SQLite, pytest, Postman, JMeter) are the design choices listed in section 3.6; none of them is mandated by the SRS.

## Python implementation notes

One Flask application serves Jinja HTML pages and the existing /api/v1 endpoints. Keep existing API payloads and requirement traceability. Use Flask-Login for identity, Flask-Session with a SQLAlchemy-backed server-side session store for logout invalidation, Flask-WTF for CSRF protection on state-changing requests, and BCrypt for salted password hashes. Role and record-ownership checks remain explicit server-side checks.

Use SQLAlchemy with SQLite on local persistent storage. Enable foreign keys on each connection, define uniqueness and capacity constraints, and use separate databases for tests and demonstrations. Do not commit database files, uploads, credentials or session secrets. SQLite serializes writers: measure the specified load and concurrency tests rather than assuming they pass. Run one application instance for the small demonstration; use a WSGI server and HTTPS for the acceptance environment. The development server alone does not satisfy HTTPS.
