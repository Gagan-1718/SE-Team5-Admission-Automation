"""Allotment services (owner: Gagan).

``get_completed_run`` and ``get_result_for_candidate`` are real (other modules need them from
Day 1). ``run_allotment`` and ``seat_consistency_report`` are contract stubs for issues #5 and
#8. Names, parameters and error types are agreed in SPRINT_TWO_START_HERE.md section 4.3.
"""
from dataclasses import dataclass

from app.extensions import db

from .models import AllotmentResult, AllotmentRun


class AllotmentError(Exception):
    status_code = 500


class AlreadyCompleted(AllotmentError):
    """A run has already completed: there is one allotment cycle (SAD A-13)."""
    status_code = 409


class NothingToAllot(AllotmentError):
    """No Eligible candidate has a locked list, so the single cycle is not spent (D2-05)."""
    status_code = 422


class RunFailed(AllotmentError):
    """The run was rolled back; nothing was saved."""
    status_code = 500


@dataclass(frozen=True)
class RunSummary:
    run_id: int
    candidates_processed: int
    allocated_count: int
    not_allocated_count: int
    duration_ms: int


def get_completed_run():
    """The completed allotment run, or None if the administrator has not run allotment yet."""
    return db.session.execute(db.select(AllotmentRun).order_by(AllotmentRun.id)).scalars().first()


def get_result_for_candidate(candidate_id):
    """The candidate's result row in the completed run, or None.

    None means the candidate was not part of the run (never locked, or not Eligible at run
    time), which is different from a ``Not Allocated`` row (D2-06).
    """
    return db.session.execute(
        db.select(AllotmentResult)
        .join(AllotmentRun, AllotmentResult.run_id == AllotmentRun.id)
        .where(AllotmentResult.candidate_id == candidate_id)
        .order_by(AllotmentRun.id)
    ).scalars().first()


def run_allotment(actor_id):
    """Run the single allotment cycle. AlreadyCompleted | NothingToAllot | RunFailed."""
    raise NotImplementedError("Contract stub: implement in issue #5.")


def seat_consistency_report():
    """A list of mismatches between seat counts and allotment records; [] means consistent."""
    raise NotImplementedError("Contract stub: implement in issue #8.")
