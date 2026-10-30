"""The candidate journey contract (SPRINT_TWO_START_HERE.md section 4.4).

Every module that owns a step of the journey has ``app/<module>/journey.py`` with
``step_statuses(candidate_id)`` returning a list of steps built with ``make_step``.
The candidate dashboard calls ``all_steps`` and never reads another module's tables.

States: ``done`` finished; ``current`` the next thing the candidate should do; ``waiting``
waiting on someone else (administrator review, automatic eligibility); ``locked`` not
available yet (``detail`` says why); ``problem`` needs the candidate's attention.
"""
import importlib

DONE, CURRENT, WAITING, LOCKED, PROBLEM = "done", "current", "waiting", "locked", "problem"
STATES = (DONE, CURRENT, WAITING, LOCKED, PROBLEM)

# The seven steps shown on the dashboard, in order, and the modules that supply them.
JOURNEY_KEYS = ("profile", "application", "documents", "eligibility", "choices", "result", "decision")
JOURNEY_MODULES = ("accounts", "application", "documents", "eligibility", "choices", "results")


def make_step(key, label, state, detail, href):
    """Build one step dict. Raises ValueError for an unknown state so typos fail loudly."""
    if state not in STATES:
        raise ValueError(f"Unknown journey state {state!r}; use one of {STATES}.")
    return {"key": key, "label": label, "state": state, "detail": detail, "href": href}


def locked_step(key, label, href, detail="Not available yet."):
    """The placeholder every module returns until its real status function is written."""
    return make_step(key, label, LOCKED, detail, href)


def all_steps(candidate_id):
    """All seven steps for the dashboard, in journey order."""
    steps = []
    for name in JOURNEY_MODULES:
        module = importlib.import_module(f"app.{name}.journey")
        steps.extend(module.step_statuses(candidate_id))
    return steps
