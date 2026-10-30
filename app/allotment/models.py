"""Allotment tables (owner: Gagan). Shape agreed in SPRINT_TWO_START_HERE.md section 4.2.

A row in ``allotment_runs`` exists only for a run that completed, because the whole run
(seat updates, results, this row, the audit entry) commits in one transaction or not at all.
The database itself allows a single cycle (SAD A-13): ``cycle`` is always 1 and unique.
"""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db

ALLOCATED = "Allocated"
NOT_ALLOCATED = "Not Allocated"
RESULT_STATUSES = (ALLOCATED, NOT_ALLOCATED)


def _now():
    return datetime.now(timezone.utc)


class AllotmentRun(db.Model):
    __tablename__ = "allotment_runs"

    id = db.Column(db.Integer, primary_key=True)
    cycle = db.Column(db.Integer, nullable=False, default=1, unique=True)
    run_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    duration_ms = db.Column(db.Integer, nullable=False, default=0)
    candidates_processed = db.Column(db.Integer, nullable=False, default=0)
    allocated_count = db.Column(db.Integer, nullable=False, default=0)
    not_allocated_count = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("cycle = 1", name="ck_allotment_runs_single_cycle"),
        CheckConstraint(
            "duration_ms >= 0 AND candidates_processed >= 0 AND allocated_count >= 0 "
            "AND not_allocated_count >= 0",
            name="ck_allotment_runs_counts_nonneg",
        ),
        # Every processed candidate is either allocated or not allocated (issue #6).
        CheckConstraint(
            "allocated_count + not_allocated_count = candidates_processed",
            name="ck_allotment_runs_counts_add_up",
        ),
    )


class AllotmentResult(db.Model):
    """One row per candidate who took part in the run (Eligible and with a locked list)."""

    __tablename__ = "allotment_results"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("allotment_runs.id"), nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rank = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    reference_number = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey("catalogue_branch.id"), nullable=True)
    seat_id = db.Column(db.Integer, db.ForeignKey("catalogue_seat.id"), nullable=True)
    choice_priority = db.Column(db.Integer, nullable=True)

    run = db.relationship("AllotmentRun")
    branch = db.relationship("Branch")
    seat = db.relationship("Seat")

    __table_args__ = (
        UniqueConstraint("run_id", "candidate_id", name="uq_allotment_results_run_candidate"),
        CheckConstraint("status IN ('Allocated', 'Not Allocated')", name="ck_allotment_results_status"),
        # Allocated means a branch, a seat and a choice number; Not Allocated means none of them.
        CheckConstraint(
            "(status = 'Allocated') = (branch_id IS NOT NULL)",
            name="ck_allotment_results_branch_matches_status",
        ),
        CheckConstraint(
            "(status = 'Allocated') = (seat_id IS NOT NULL)",
            name="ck_allotment_results_seat_matches_status",
        ),
        CheckConstraint(
            "(status = 'Allocated') = (choice_priority IS NOT NULL)",
            name="ck_allotment_results_priority_matches_status",
        ),
    )
