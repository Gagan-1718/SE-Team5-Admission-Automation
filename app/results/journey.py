"""Journey steps for the candidate dashboard (SPRINT_TWO_START_HERE.md section 4.4).

STUB: returns both steps as locked until the module owner writes the real status logic.
The Result module supplies two steps: the allotment result and the seat decision.
"""
from app.journey import locked_step


def step_statuses(candidate_id):
    return [
        locked_step("result", "Allotment result", "/result",
                    "Visible after the administrator publishes results."),
        locked_step("decision", "Seat decision", "/result",
                    "Accept or reject once your result is published."),
    ]
