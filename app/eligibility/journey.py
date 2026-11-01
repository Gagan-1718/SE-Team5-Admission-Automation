"""Eligibility journey step for the candidate dashboard."""

from app.journey import DONE, PROBLEM, WAITING, make_step
from app.eligibility.evaluation import PENDING, ELIGIBLE, NOT_ELIGIBLE
from app.eligibility.services import get_eligibility

KEY = "eligibility"
LABEL = "Eligibility"
HREF = "/eligibility"


def step_statuses(candidate_id):
    """Return the candidate's current eligibility journey step."""
    result = get_eligibility(candidate_id)
    status = result["status"]

    if status == PENDING:
        state = WAITING
    elif status == NOT_ELIGIBLE:
        state = PROBLEM
    elif status == ELIGIBLE:
        state = DONE
    else:
        raise ValueError(f"Unknown eligibility status: {status!r}")

    return [
        make_step(
            KEY,
            LABEL,
            state,
            result["reason"],
            HREF,
        )
    ]
