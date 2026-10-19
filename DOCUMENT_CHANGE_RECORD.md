# Python migration document record

Decision: 19 October 2026, adopt Python Flask and SQLite for the small academic demonstration. Keep the existing functional/security requirements and mock-data scope.

| Document | Treatment |
|---|---|
| SRS_Draft.md and SRS_Team5_Admission_Automation.pdf | Reviewed for stack-specific requirements; no Java/Spring/MySQL mandate found. Keep requirements unchanged. |
| SAD_Team5_Admission_Automation.docx | Revised local copy: version 1.2, stack, tools, assumptions, SQLite transaction/audit safeguards and Python implementation notes. Word visual QA is pending because the bundled renderer cannot find LibreOffice. Use the Markdown architecture copy for immediate review. |
| TestPlan_Team5_Admission_Automation.pdf | Keep original cases; apply TEST_PLAN_PYTHON_ADDENDUM.md for environment and revised proposed schedule. Original PDF has not been rewritten. |
| Team 5 – Admission Automation Project.md | Original project brief retained; SRS scope and exclusions continue to govern. |
| README.md | Explains the chosen stack and document order without claiming implementation exists. |
| Earlier delivery plan | Superseded for stack and dates by SPRINT_ONE_START_HERE.md; retain earlier material as historical planning. |

The Markdown revisions in this change supersede the old technology choices; original Word/PDF files remain available as historical references and for unchanged diagrams/test cases. Existing requirements remain unchanged. The revised Word copy is held locally and must pass rendering before publication. This documentation change does not complete the setup implementation issue.
