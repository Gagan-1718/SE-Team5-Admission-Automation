"""Allotment services (owner: Gagan).

``run_allotment`` is the single allotment cycle (issues #5 and #6). It follows SAD A-07:
take the database write lock first, then check that no run has completed, then load,
allot, write and commit. The seat updates, the result rows, the run row and the audit entry
are saved together or not at all. ``seat_consistency_report`` is the check for issue #8.
Names, parameters and error types are agreed in SPRINT_TWO_START_HERE.md section 4.3.
"""
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from flask import current_app
from sqlalchemy import func, text

from app.accounts.services import get_exam_details
from app.application.services import get_submitted_application
from app.audit.services import record_audit
from app.catalogue.models import Seat
from app.choices.services import get_locked_branch_ids, locked_candidate_ids
from app.documents.services import all_documents_approved
from app.eligibility.evaluation import ELIGIBLE, evaluate_eligibility
from app.eligibility.models import EligibilityRule
from app.extensions import db

from .engine import allot
from .models import ALLOCATED, AllotmentResult, AllotmentRun


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


def _now():
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------- lookups
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


def load_candidates():
    """Everyone with a locked list, as input for ``allot``; ``eligible`` is checked now.

    Eligibility is evaluated at run time, not when the list was locked (D2-06): a cut-off
    or a document may have changed since. Rules are loaded once for the whole run.
    Candidates with a lock but no exam details or no submitted application cannot take part.
    """
    rules = db.session.execute(db.select(EligibilityRule)).scalars().all()
    candidates = []
    for candidate_id in locked_candidate_ids():
        details = get_exam_details(candidate_id)
        application = get_submitted_application(candidate_id)
        if details is None or application is None:
            continue
        decision = evaluate_eligibility(
            details["rank"], details["category"], all_documents_approved(candidate_id), rules
        )
        candidates.append({
            "candidate_id": candidate_id,
            "rank": details["rank"],
            "reference": application.reference_number,
            "category": details["category"],
            "branch_ids": get_locked_branch_ids(candidate_id),
            "eligible": decision["status"] == ELIGIBLE,
        })
    return candidates


# ----------------------------------------------------------------- the run
def _begin_write_transaction():
    """Take SQLite's write lock before reading anything, so two runs cannot interleave."""
    db.session.rollback()
    if db.engine.dialect.name == "sqlite":
        db.session.execute(text("BEGIN IMMEDIATE"))


def _take_seat(seat_id):
    """Add one to ``filled``. The WHERE clause means even a logic bug cannot pass capacity."""
    result = db.session.execute(
        db.update(Seat)
        .where(Seat.id == seat_id, Seat.filled < Seat.capacity)
        .values(filled=Seat.filled + 1)
    )
    if result.rowcount != 1:
        raise RuntimeError(f"Seat row {seat_id} has no free seat left.")


def _record_failure(actor_id):
    try:
        record_audit(actor_id, "allotment.run", "allotment_run", None, outcome="Failed")
    except Exception:  # never hide the original failure behind an audit problem
        db.session.rollback()
        current_app.logger.exception("Could not record the failed allotment run")


def run_allotment(actor_id):
    """Run the single allotment cycle. AlreadyCompleted | NothingToAllot | RunFailed."""
    started_clock = time.perf_counter()
    started_at = _now()
    try:
        _begin_write_transaction()
        if get_completed_run() is not None:
            raise AlreadyCompleted("Allotment has already been run. There is one cycle only.")

        candidates = load_candidates()
        if not any(c["eligible"] for c in candidates):
            raise NothingToAllot("No eligible candidate has locked their choices yet.")

        seats = db.session.execute(db.select(Seat)).scalars().all()
        free = {(s.branch_id, s.category): s.capacity - s.filled for s in seats}
        seat_ids = {(s.branch_id, s.category): s.id for s in seats}
        results = allot(candidates, free)
        allocated = sum(1 for r in results if r["status"] == ALLOCATED)

        run = AllotmentRun(
            run_by=actor_id,
            started_at=started_at,
            candidates_processed=len(results),
            allocated_count=allocated,
            not_allocated_count=len(results) - allocated,
        )
        db.session.add(run)
        db.session.flush()

        for r in results:
            seat_id = seat_ids[(r["branch_id"], r["category"])] if r["status"] == ALLOCATED else None
            db.session.add(AllotmentResult(
                run_id=run.id,
                candidate_id=r["candidate_id"],
                rank=r["rank"],
                category=r["category"],
                reference_number=r["reference"],
                status=r["status"],
                branch_id=r["branch_id"],
                seat_id=seat_id,
                choice_priority=r["choice_priority"],
            ))
            if seat_id is not None:
                _take_seat(seat_id)

        run.completed_at = _now()
        run.duration_ms = int((time.perf_counter() - started_clock) * 1000)
        record_audit(actor_id, "allotment.run", "allotment_run", run.id, commit=False)
        db.session.commit()
    except (AlreadyCompleted, NothingToAllot):
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Allotment run failed and was rolled back")
        _record_failure(actor_id)
        raise RunFailed("The allotment run failed and nothing was saved. Try again.") from exc

    return RunSummary(
        run_id=run.id,
        candidates_processed=run.candidates_processed,
        allocated_count=run.allocated_count,
        not_allocated_count=run.not_allocated_count,
        duration_ms=run.duration_ms,
    )


# ----------------------------------------------------------------- consistency (#8)
def seat_consistency_report():
    """A list of mismatches between seat counts and allotment records; [] means consistent.

    For every college-branch-category seat row, ``filled`` must equal the number of
    Allocated results that point at it, and must not exceed ``capacity`` (ADM-NFR-003).
    """
    allocated = dict(db.session.execute(
        db.select(AllotmentResult.seat_id, func.count())
        .where(AllotmentResult.status == ALLOCATED)
        .group_by(AllotmentResult.seat_id)
    ).all())
    mismatches = []
    for seat in db.session.execute(db.select(Seat).order_by(Seat.id)).scalars():
        records = int(allocated.get(seat.id, 0))
        if seat.filled != records or seat.filled > seat.capacity:
            mismatches.append({
                "seat_id": seat.id,
                "branch_id": seat.branch_id,
                "category": seat.category,
                "capacity": seat.capacity,
                "filled": seat.filled,
                "allocated_records": records,
            })
    return mismatches
