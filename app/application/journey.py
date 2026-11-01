"""Journey step for the candidate dashboard (SPRINT_TWO_START_HERE.md section 4.4)."""
from app.accounts.services import get_exam_details
from app.journey import CURRENT, DONE, LOCKED, make_step

from .services import get_for_candidate

KEY, LABEL, HREF = "application", "Application", "/application"


def step_statuses(candidate_id):
    application = get_for_candidate(candidate_id)
    if application is not None and not application.is_draft:
        return [make_step(KEY, LABEL, DONE, f"Submitted as {application.reference_number}.", HREF)]
    if get_exam_details(candidate_id) is None:
        if application is None:
            return [make_step(KEY, LABEL, LOCKED, "Enter your exam details first.", HREF)]
        return [make_step(KEY, LABEL, CURRENT, "Draft saved. Enter your exam details so you can submit.", HREF)]
    if application is None:
        return [make_step(KEY, LABEL, CURRENT, "Start your application.", HREF)]
    return [make_step(KEY, LABEL, CURRENT, "Draft saved. Fill in every field and submit.", HREF)]
