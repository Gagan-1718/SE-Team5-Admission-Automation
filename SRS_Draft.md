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
