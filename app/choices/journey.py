"""Choice-filling journey state for the candidate dashboard."""

from app.eligibility.services import get_eligibility
from app.journey import make_step

from .services import is_locked


def step_statuses(candidate_id):
    eligibility = get_eligibility(candidate_id)
    if eligibility.get("status") != "Eligible":
        detail = eligibility.get("reason") or "Choice filling is unavailable until you are Eligible."
        state = "locked"
    elif is_locked(candidate_id):
        detail = "Your choice list is locked and ready for allotment."
        state = "done"
    else:
        detail = "Add and order your preferred college branches."
        state = "current"
    return [make_step("choices", "Choices", state, detail, "/choices")]
