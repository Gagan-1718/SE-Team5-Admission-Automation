"""Result and decision journey steps for the shared candidate dashboard."""
from app.journey import make_step
from .services import ALLOCATED, NOT_ALLOCATED, NOT_IN_RUN, NOT_PUBLISHED, candidate_view


def step_statuses(candidate_id):
    view = candidate_view(candidate_id)
    state = view["state"]
    if state == NOT_PUBLISHED:
        result_state, detail = "locked", "Visible after the administrator publishes results."
    elif state == NOT_ALLOCATED:
        result_state, detail = "problem", "No seat was available for your locked choices."
    elif state == NOT_IN_RUN:
        result_state, detail = "problem", "You were not part of this allotment run."
    else:
        result_state, detail = "done", "Your published allotment result is available."
    if state != ALLOCATED:
        decision_state, decision_detail = "locked", "A published allocated seat is required."
    elif view["decision"]:
        decision_state, decision_detail = "done", "Seat " + view["decision"]["decision"].lower() + "."
    else:
        decision_state, decision_detail = "current", "Accept or reject your allotted seat once."
    return [
        make_step("result", "Allotment result", result_state, detail, "/result"),
        make_step("decision", "Seat decision", decision_state, decision_detail, "/result"),
    ]
