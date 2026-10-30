"""Journey step for the candidate dashboard (SPRINT_TWO_START_HERE.md section 4.4).

STUB: returns the step as locked until the module owner writes the real status logic.
"""
from app.journey import locked_step


def step_statuses(candidate_id):
    return [locked_step("eligibility", "Eligibility", "/eligibility")]
