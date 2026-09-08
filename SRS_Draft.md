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
