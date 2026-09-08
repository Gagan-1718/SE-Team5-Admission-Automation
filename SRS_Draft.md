# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional, non-functional, and security requirements for the Automated Engineering Admission & Counselling Management Platform, a web-based system that supports a KCET/COMEDK-style engineering admission and seat-counselling workflow. This document guides the design, implementation, and testing of the system by a four-member Software Engineering project team, and serves as the basis for verifying that the delivered system meets its agreed scope. Every requirement in this document represents functionality the project team commits to implementing; scope has been deliberately kept realistic for a single academic project cycle.

## 1.2 Scope

The system enables engineering admission candidates to register, submit applications, upload supporting documents, check eligibility against configured (mock/seeded) exam data, browse participating colleges and branches, fill and lock ranked preferences, and view and act on seat allotment results. It enables administrators to manage candidate records, verify documents, manage the college/branch/seat catalogue, run a rank-and-preference-based seat allotment engine, publish results, and review a basic audit trail.

The system is an educational prototype that follows the general structure of real KCET/COMEDK counselling workflows. It does not integrate with, and does not claim to be, the official Karnataka Examinations Authority (KEA) or COMEDK systems. The following are explicitly out of scope: real KEA/COMEDK API integration, OCR or AI-based document verification, Aadhaar or biometric authentication, offline/kiosk modes, real payment or SMS gateways, mandatory external email services, medical/dental admissions, post-admission academic management, in-app notifications, multiple/subsequent counselling rounds, and any AI-based prediction, recommendation, or graph-analytics functionality. A single allotment cycle is implemented; support for multiple rounds is noted only as a possible future enhancement, not as a requirement.

## 1.3 Audience

This document is intended for the student project team (developers and testers), the project guide/faculty evaluator, and any reviewer assessing the completeness and testability of the requirements for academic evaluation purposes.

## 1.4 Definitions and Glossary

| Term | Definition |
|---|---|
| Candidate | A prospective engineering student who registers on the platform to seek admission. |
| Administrator (Admin) | The single platform-operator role, responsible for document verification, college/branch/seat-matrix management, running allotment, publishing results, and reviewing audit logs. |
| Application | A candidate's formally submitted request for admission, identified by a unique reference number. |
| Eligibility | A candidate's qualification status for admission, determined against configured, seeded exam-based rules. |
| Choice | A candidate-selected college-branch combination, ranked by preference. |
| Seat Matrix | The configured record of total, filled, and available seats per college, branch, and category. |
| Allotment Run | A single execution of the seat allotment engine over the current candidate pool and seat matrix. This project implements one allotment cycle; it is not divided into multiple counselling rounds. |
| Not Allocated | An allotment outcome indicating no locked preference could be satisfied for a candidate in the allotment run. |
| KCET | Karnataka Common Entrance Test — a state-level engineering entrance examination, referenced here only as a workflow model, using mock/seeded data. |
| COMEDK | Consortium of Medical, Engineering and Dental Colleges of Karnataka — a private engineering admission body, referenced here only as a workflow model, using mock/seeded data. |
| RTM | Requirements Traceability Matrix — maps requirements to design, implementation, and test artifacts. |
| NFR | Non-Functional Requirement. |
| RBAC | Role-Based Access Control. |

# 2. Overall Description

## 2.1 Product Perspective

The platform is a new, standalone, web-based application. It is not a replacement for, and does not interface with, official KEA/COMEDK systems. It uses mock/seeded exam data and configurable, admin-managed catalogue and eligibility data so the full admission-to-allotment workflow can be demonstrated end-to-end within a college project's scope.

## 2.2 Major Product Functions

- Candidate registration, authentication, and profile/exam-detail management.
- Application creation, draft-saving, editing, and submission with reference-number generation.
- Document upload, admin verification, and resubmission of rejected documents.
- Eligibility checking against configured, seeded exam rules.
- Data-driven college/branch catalogue browsing and admin seat-matrix management.
- Choice filling, reordering, and locking.
- Rank + preference + seat-availability based seat allotment (single allotment cycle).
- Allotment result publication and viewing.
- Seat acceptance or rejection/withdrawal.
- Administrative oversight and basic audit logging.

## 2.3 User Roles and Characteristics

| Role | Characteristics / Responsibilities |
|---|---|
| Candidate | Prospective student; registers, applies, uploads documents, fills and locks choices, views results, and makes a seat decision. Assumed to have basic web-literacy and no specialised training. |
| Administrator | The single operator role. Reviews and verifies uploaded documents; manages candidates, colleges, branches, and the seat matrix; runs allotment; publishes results; and reviews audit logs. Assumed to be a trained platform operator. |

## 2.4 Operating Environment

- Client: Modern desktop or mobile web browser (e.g., Chrome, Firefox, Edge).
- Server: Standard web application server and relational or document database, deployable on a typical development or college-lab environment.
- No specialised hardware, kiosk terminals, or government network access is required.

## 2.5 Constraints

- The system must be implementable by a four-member team within a single academic semester/project cycle.
- Exam and eligibility data are mock/seeded, not sourced from real KEA/COMEDK systems.
- No payment functionality, real or simulated, is implemented.
- The system is designed and demonstrated for a small-to-moderate dataset (tens to a few hundred candidate records), not for real-world admission volumes.


# 3. External Interface Requirements

## 3.1 User Interfaces

The system shall provide a responsive, browser-based web interface with distinct candidate and administrator views. Candidate screens include registration/login, profile and exam details, application form, document upload, eligibility status, college/branch catalogue, choice filling and locking, allotment result, and seat decision. Administrator screens include candidate management, document verification, college/branch/seat-matrix management, allotment execution, result publication, and audit log viewing.

## 3.2 Hardware Interfaces

No specialised hardware interfaces are required. The system operates on standard client devices (desktop or mobile) with a network connection; no biometric, kiosk, or dedicated scanning hardware is assumed.

## 3.3 Software Interfaces

- Web browser (client-side rendering).
- Application server / backend framework (team's implementation choice).
- Relational or document database for candidates, applications, documents, colleges, seat matrix, and audit logs.
- No external KEA, COMEDK, payment gateway, or SMS gateway software interfaces are used.

## 3.4 Communications

All client-server communication shall occur over HTTPS. No external email or SMS communication channel is required.

# 4. System Features

This section presents functional requirements grouped by feature area. Each requirement is atomic, testable, and traceable to the Requirements Traceability Matrix in Section 8. Requirement IDs follow the pattern ADM-F-NNN.

## 4.1 Candidate Account Management

These requirements cover candidate registration, authentication, profile management, and exam-detail capture that together establish a candidate's identity within the platform.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-001 | The system shall allow a new candidate to register an account by providing name, email address, mobile number, date of birth, and a password. | High | Candidate | TC-001: Given valid, unique registration details, the system creates an account and displays a confirmation. Duplicate email/mobile is rejected. | Feeds ADM-F-002 |
| ADM-F-002 | The system shall allow a registered candidate to log in and log out using a registered email/mobile number and password. | High | Candidate | TC-002: Given correct credentials, the candidate is authenticated and redirected to the dashboard; given incorrect credentials, an error is shown and access is denied. | Depends on ADM-F-001; related to SEC-F-001 |
| ADM-F-003 | The system shall allow a logged-in candidate to view and update profile information (contact details, address) and to enter exam details — exam type (KCET/COMEDK), rank, category, and score — using mock/seeded exam data. | High | Candidate | TC-003: Given a valid profile edit, changes are saved and reflected on the profile page. Given exam details matching a seeded record, the rank and category are stored against the candidate. | Depends on ADM-F-002. Feeds ADM-F-005, ADM-F-009 |

## 4.2 Application Management

These requirements cover the creation, editing, and formal submission of a candidate's admission application.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-004 | The system shall allow a candidate to create and save an application as a draft prior to final submission. | High | Candidate | TC-004: Given partially filled application data, the candidate can save and later resume the draft without data loss. | Depends on ADM-F-003 |
| ADM-F-005 | The system shall allow a candidate to edit a draft application and submit it once all mandatory fields are complete, generating a unique, non-reusable application reference number upon successful submission. | High | Candidate | TC-005: Given a complete draft, submission is accepted, the status changes to 'Submitted', and a unique reference number is generated and displayed. An incomplete draft is rejected with field-level errors. | Depends on ADM-F-004. Reference number is used across documents, eligibility, and allotment records. |

## 4.3 Document Upload and Verification

These requirements cover upload, validation, and administrative verification of supporting admission documents.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-006 | The system shall allow a candidate to upload required admission documents, validating file type (PDF/JPEG/PNG) and maximum file size before acceptance. | High | Candidate | TC-006: Given a file within the allowed type and size, upload succeeds; given an invalid type or oversized file, upload is rejected with an explanatory message. | Depends on ADM-F-005 |
| ADM-F-007 | The system shall allow the administrator to review uploaded documents and mark each as Approved or Rejected, recording a rejection reason where applicable. | High | Administrator | TC-007: Given a rejected document, a mandatory rejection reason is stored and visible to the candidate. | Depends on ADM-F-006; related to SEC-F-002 (role-based access) |
| ADM-F-008 | The system shall allow a candidate to view the verification status of each uploaded document and resubmit a document that has been rejected. | Medium | Candidate | TC-008: Given a rejected document, the candidate can upload a replacement, which resets its status to Pending Verification. | Depends on ADM-F-007 |

## 4.4 Eligibility Verification

This requirement covers automated checking of candidate eligibility against configured, seeded exam-based rules and presentation of a basic result reason.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-009 | The system shall evaluate a candidate's submitted exam details and category against configured eligibility rules, return a status of Eligible, Not Eligible, or Pending Verification, and display a basic, human-readable reason accompanying a Not Eligible or Pending Verification result. | High | Candidate / Admin | TC-009: Given seeded exam data and a configured rule set, the system returns the correct eligibility status and a reason that reflects the specific rule not satisfied, for at least three representative cases (eligible, not eligible, pending). | Depends on ADM-F-003 and ADM-F-007 (document verification may affect final status). Feeds ADM-F-012 |

## 4.5 College, Branch and Seat Management

These requirements cover candidate-facing browsing of colleges and branches, and admin-managed catalogue and seat-matrix data.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-010 | The system shall allow a candidate to view a catalogue of participating colleges and their offered branches, including current seat availability, with an optional lightweight filter by college or branch name. | Medium | Candidate | TC-010: Given a filter term, only matching colleges or branches are displayed; seat-availability figures shown match the underlying seat matrix. | Depends on ADM-F-011 |
| ADM-F-011 | The system shall allow the administrator to add, edit, and configure colleges, branches, and category-wise seat capacity in a data-driven manner, with seat availability updating automatically after each allotment run. | High | Administrator | TC-011: Given a new college/branch record with seat capacity, it becomes immediately visible in the candidate catalogue and available for choice filling and allotment. After a completed allotment run, seat counts reflect the number of candidates allotted to each college-branch-category combination. | Feeds ADM-F-010, ADM-F-013, ADM-F-015 |

## 4.6 Choice Filling

These requirements cover the candidate's selection, ordering, and locking of college-branch preferences prior to allotment.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-012 | The system shall allow an eligible candidate to add, remove, and preview college-branch choices, preventing the addition of duplicate choices. | High | Candidate | TC-012: Given a choice already in the candidate's list, attempting to add it again is rejected with a duplicate-choice message. | Depends on ADM-F-009 (eligibility) and ADM-F-010 (catalogue) |
| ADM-F-013 | The system shall allow a candidate to reorder saved choices to reflect priority before locking. | Medium | Candidate | TC-013: Given a reordering action, the saved choice-priority sequence is updated and persisted. | Depends on ADM-F-012 |
| ADM-F-014 | The system shall allow a candidate to lock/freeze their choice list, after which no further additions, removals, or reordering are permitted. | High | Candidate | TC-014: Given a locked choice list, any attempt to modify it is rejected, and the list is used as-is for allotment. | Depends on ADM-F-013. Feeds ADM-F-015 |

## 4.7 Seat Allotment

This is the central algorithmic component of the system: a rank, preference, and seat-availability based allotment engine, triggered by the administrator and executed as a single allotment cycle.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-015 | The system shall, when an administrator runs allotment, process eligible candidates in ascending order of rank and, for each candidate, allocate the first locked preference (in the candidate's saved order) that is eligible and has an available seat, reducing seat availability immediately after each allocation. | High | Admin / System | TC-015: Given a seeded dataset of candidates, ranks, preferences, and a seat matrix, the allotment run produces allocations consistent with rank order, preference order, seat capacity, and eligibility/category rules, verified against a hand-computed expected result. | Depends on ADM-F-009, ADM-F-011, ADM-F-014. Core requirement of the system |
| ADM-F-016 | The system shall mark a candidate as Not Allocated if none of their locked preferences can be satisfied during the allotment run. | High | System | TC-016: Given a candidate whose preferences are all unavailable or ineligible, the result for that candidate is recorded as Not Allocated. | Depends on ADM-F-015 |

## 4.8 Allotment Result and Seat Decision

These requirements cover candidate-facing publication of the allotment outcome and the candidate's subsequent decision on an allotted seat.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-017 | The system shall allow the administrator to publish allotment results for the completed allotment run, making them visible to candidates only after publication. | High | Administrator | TC-017: Given an unpublished result, candidates cannot view it; after publication, results become visible immediately. | Depends on ADM-F-015 |
| ADM-F-018 | The system shall allow a candidate to view their allotment result, including the allotted college/branch (if any) and the allocation status. | High | Candidate | TC-018: Given a published result, the candidate sees the correct allotted college/branch and status (Allocated/Not Allocated). | Depends on ADM-F-015, ADM-F-016, ADM-F-017 |
| ADM-F-019 | The system shall allow a candidate with a published allotment result to accept or reject/withdraw the allotted seat, exactly once. | High | Candidate | TC-019: Given a published result, each of Accept and Reject/Withdraw is available exactly once and correctly updates the candidate's seat-decision status. | Depends on ADM-F-018 |

## 4.9 Administration and Audit

This requirement covers consolidated administrative oversight of candidates, applications, and documents. Audit logging of privileged actions is defined as a security requirement (SEC-F-005) to avoid duplicating the same capability in two sections.

| ID | Requirement ("The system shall...") | Priority | Source | Acceptance Criteria | Dependencies |
|---|---|---|---|---|---|
| ADM-F-020 | The system shall allow the administrator to view and manage candidate records, application statuses, and document-verification queues from a consolidated dashboard. | Medium | Administrator | TC-020: Given the admin dashboard, candidate counts, statuses, and pending-verification queues match the underlying data. | Depends on ADM-F-001, ADM-F-005, ADM-F-007, ADM-F-011 |

# 5. Non-Functional Requirements

Exactly five non-functional requirements (NFRs) are defined, each measurable and realistic for a college-scale project.

| ID | Category | Priority | Requirement | Acceptance Criterion / Measurement |
|---|---|---|---|---|
| ADM-NFR-001 | Performance | High | The system shall respond to standard candidate-facing page requests (login, catalogue view, choice filling) within 2 seconds under normal load in the demonstration environment. | Verified by informal timing or a lightweight load-testing tool during a demo walkthrough; average observed response time does not exceed 2 seconds. |
| ADM-NFR-002 | Scalability | Medium | The seat allotment engine shall complete an allotment run for the project's demonstration dataset (up to a few hundred candidates) within a reasonable time, without requiring architectural changes for moderate increases in data volume. | An allotment run over the full seeded demonstration dataset completes within an agreed time limit (e.g., under 1 minute) during testing. |
| ADM-NFR-003 | Reliability / Data Consistency | High | The system shall ensure that seat availability counts remain consistent with actual allotment records at all times, with no allocation exceeding configured seat capacity. | After any allotment run, for every college-branch-category combination, allotted count does not exceed configured seat capacity, verified programmatically or by test script. |
| ADM-NFR-004 | Usability | Medium | The system shall present candidate-facing workflows (registration through seat decision) so that a first-time user can complete application submission without external assistance. | In an informal walkthrough with a small number of test users, the majority complete application submission without assistance. |
| ADM-NFR-005 | Maintainability | Medium | The system shall keep college, branch, seat-matrix, and eligibility-rule data fully configurable through admin interfaces rather than hardcoded in application logic. | Adding a new college/branch/rule requires only admin-interface actions and no source-code changes, verified by walkthrough. |

## 5.1 Security

### 5.1.1 Security Objectives

- Objective 1: Protect candidate personal and application data from unauthorized access.
- Objective 2: Ensure only authorized administrators can perform privileged admission/seat-management operations.
- Objective 3: Preserve integrity and traceability of important admission actions.

### 5.1.2 Security Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| SEC-F-001 | The system shall require successful authentication (email/mobile and password) before granting access to any candidate or administrator functionality. | High | TC-021: Unauthenticated requests to protected endpoints/pages are redirected to login and denied access to protected data. |
| SEC-F-002 | The system shall enforce role-based access control, restricting administrative functions to users assigned the Administrator role. | High | TC-022: A candidate-role account attempting to access an admin-only function (e.g., publish results) is denied with an authorization error. |
| SEC-F-003 | The system shall store candidate and administrator passwords using a salted cryptographic hash and shall never store or log plaintext passwords. | High | TC-023: Inspection of the credential store confirms only salted hashes are present; no plaintext password appears in application logs. |
| SEC-F-004 | The system shall transmit all candidate and administrator data, including credentials, over an encrypted (HTTPS/TLS) connection. | High | TC-024: Network traffic capture during login and data-entry operations shows encrypted transport with no plaintext credentials or personal data on the wire. |
| SEC-F-005 | The system shall record an audit log entry, including actor identity, timestamp, and action type, for every privileged administrative action affecting candidate, seat-matrix, or allotment data. | Medium | TC-025: Given a privileged action (e.g., seat-matrix edit, allotment run, result publication), a corresponding audit entry is created and is not editable through the standard UI. |

# 6. Quality Attributes & Acceptance Tests

Beyond the measurable NFRs in Section 5, the system is expected to exhibit correctness (especially in the allotment engine), consistency (seat counts always reconcile with allotment records), and traceability (every privileged action is auditable). The table below defines concise, workflow-level acceptance criteria; each maps to one or more detailed test cases referenced in Section 8.

| Workflow | Acceptance Criteria |
|---|---|
| Candidate Registration | A new candidate with unique, valid details can register and receives account confirmation; duplicate email/mobile is rejected. |
| Application Submission | A candidate can save a draft, resume it, and submit only when all mandatory fields are valid; submission yields a unique reference number. |
| Document Upload & Verification | Only allowed file types/sizes are accepted; the administrator can approve or reject with a reason; a rejected document can be resubmitted and moves back to Pending Verification. |
| Eligibility Check | Given seeded exam data, the system returns Eligible, Not Eligible, or Pending Verification with a correct accompanying reason for at least three representative cases. |
| Choice Filling and Locking | A candidate can add non-duplicate eligible choices, reorder them, and lock the list; no modification is possible after locking. |
| Seat Allotment (core algorithm) | Across a seeded test dataset the allotment run demonstrates: candidates are processed strictly in ascending rank order; each candidate's preferences are considered in declared priority order; an allocation is made only where a seat is available in that college-branch-category; only eligible candidates receive an allocation; seat-availability counts decrease correctly and immediately after each allocation, with no combination exceeding configured capacity; a candidate with no satisfiable preference is correctly marked Not Allocated. |
| Allotment Result Publication | Results are hidden from candidates until the administrator publishes the allotment run; after publication, each candidate sees the correct allotted college/branch and status. |
| Seat Acceptance/Rejection | A candidate with a published result can Accept or Reject/Withdraw exactly once, and the recorded decision status updates accordingly. |
| Admin Access Control | A non-admin account is denied access to seat-matrix management, allotment execution, and result publication; an admin account can perform all of these. |

# 7. System Models / UML Use-Case Diagrams

Two use-case diagrams model the system's primary actors and their interactions.

## 7.1 Diagram 1: Candidate Admission & Counselling

**Actor:** Candidate

**Use cases:**
- Register/Login
- Manage Profile
- Enter Exam Details
- Submit Application
- Upload Documents
- Check Eligibility
- View Colleges/Branches
- Fill Choices
- Reorder Choices
- Lock Choices
- View Allotment
- Accept/Reject Seat

## 7.2 Diagram 2: Administrator & Allotment Management

**Actor:** Administrator

**Use cases:**
- Manage Candidates
- Verify Documents
- Verify Eligibility
- Manage Colleges
- Manage Branches
- Manage Seat Matrix
- Run Allotment
- Publish Results
- View Audit Logs

**Relationship notes:**
- Submit Application includes Register/Login.
- Fill Choices includes Check Eligibility.
- Lock Choices includes Reorder Choices.
- View Allotment presumes Lock Choices has occurred.
- Run Allotment presumes Manage Seat Matrix is configured.
- Publish Results presumes Run Allotment has completed.

# 8. Requirements Traceability Matrix (RTM)

The RTM below maps every functional, non-functional, and security requirement to its SRS section, implementation module, and test case reference. Status values (Planned/Implemented/Tested/Verified) are to be updated by the team as development proceeds; all entries below are recorded at 'Planned' status as of this document version.

| Req. ID | Summary | SRS § | Module | Test Case | Status |
|---|---|---|---|---|---|
| ADM-F-001 | Candidate registration | 4.1 | Account Module | TC-001 | Planned |
| ADM-F-002 | Candidate login/logout | 4.1 | Account Module | TC-002 | Planned |
| ADM-F-003 | Candidate profile & exam-detail management | 4.1 | Account Module | TC-003 | Planned |
| ADM-F-004 | Save application as draft | 4.2 | Application Module | TC-004 | Planned |
| ADM-F-005 | Edit, submit application; generate reference number | 4.2 | Application Module | TC-005 | Planned |
| ADM-F-006 | Document upload and validation | 4.3 | Document Module | TC-006 | Planned |
| ADM-F-007 | Document verification (approve/reject) | 4.3 | Document Module | TC-007 | Planned |
| ADM-F-008 | Document status view and resubmission | 4.3 | Document Module | TC-008 | Planned |
| ADM-F-009 | Eligibility calculation and reason display | 4.4 | Eligibility Module | TC-009 | Planned |
| ADM-F-010 | College/branch catalogue view | 4.5 | Catalogue Module | TC-010 | Planned |
| ADM-F-011 | Admin college/branch/seat management | 4.5 | Catalogue Module | TC-011 | Planned |
| ADM-F-012 | Choice add/remove/preview | 4.6 | Choice Module | TC-012 | Planned |
| ADM-F-013 | Choice reordering | 4.6 | Choice Module | TC-013 | Planned |
| ADM-F-014 | Choice locking | 4.6 | Choice Module | TC-014 | Planned |
| ADM-F-015 | Rank/preference/seat-based allotment engine | 4.7 | Allotment Module | TC-015 | Planned |
| ADM-F-016 | Not Allocated determination | 4.7 | Allotment Module | TC-016 | Planned |
| ADM-F-017 | Allotment result publication | 4.8 | Result Module | TC-017 | Planned |
| ADM-F-018 | Allotment result viewing | 4.8 | Result Module | TC-018 | Planned |
| ADM-F-019 | Seat accept/reject decision | 4.8 | Result Module | TC-019 | Planned |
| ADM-F-020 | Admin candidate/application dashboard | 4.9 | Admin Module | TC-020 | Planned |
| ADM-NFR-001 | Response time performance | 5 | Cross-cutting | TC-026 | Planned |
| ADM-NFR-002 | Allotment run scalability | 5 | Allotment Module | TC-027 | Planned |
| ADM-NFR-003 | Seat-count data consistency | 5 | Allotment Module | TC-028 | Planned |
| ADM-NFR-004 | Candidate workflow usability | 5 | Cross-cutting | TC-029 | Planned |
| ADM-NFR-005 | Configurable, data-driven maintainability | 5 | Catalogue Module | TC-030 | Planned |
| SEC-F-001 | Mandatory authentication | 5.1.2 | Account Module | TC-021 | Planned |
| SEC-F-002 | Role-based access control | 5.1.2 | Account Module | TC-022 | Planned |
| SEC-F-003 | Salted password hashing | 5.1.2 | Account Module | TC-023 | Planned |
| SEC-F-004 | Encrypted data in transit | 5.1.2 | Cross-cutting | TC-024 | Planned |
| SEC-F-005 | Audit logging of privileged actions | 5.1.2 | Audit Module | TC-025 | Planned |

# Assumptions

- All exam ranks, categories, and eligibility rules used in the project are mock/seeded data and do not represent real candidates or real KEA/COMEDK data.
- The project team has access to a standard web development stack and a database of the team's choosing; no specific framework is mandated by this SRS.
- The demonstration dataset size (tens to a few hundred candidates) is sufficient to validate the correctness of the allotment engine for academic evaluation purposes.
- No payment functionality, real or simulated, is required for the demonstrated workflow.
- Document verification is performed manually by the Administrator; no OCR or AI-based automated verification is implemented.
- A single allotment cycle is sufficient to demonstrate the allotment engine; multiple counselling rounds are not implemented and are noted only as a possible future enhancement.

# References

- Institution-provided SRS template
- Team's prior C-based COMEDK admission/allotment project
- Publicly available descriptions of KCET and COMEDK counselling workflows
