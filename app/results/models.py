"""Result tables (owner: Dikshith). Shape agreed in SPRINT_TWO_START_HERE.md section 4.2.

"Published" is stored here, not as a status on the allotment run, so the Result module owns
it (decision D2-08). Both "publish once" and "decide once" are database rules, not just
disabled buttons: a second row for the same run or the same result is refused.
"""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from app.extensions import db

ACCEPTED = "Accepted"
REJECTED = "Rejected"
DECISIONS = (ACCEPTED, REJECTED)


def _now():
    return datetime.now(timezone.utc)


class ResultPublication(db.Model):
    __tablename__ = "result_publications"

    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("allotment_runs.id"), nullable=False, unique=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    published_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    run = db.relationship("AllotmentRun")


class SeatDecision(db.Model):
    __tablename__ = "seat_decisions"

    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey("allotment_results.id"), nullable=False, unique=True)
    decision = db.Column(db.String(20), nullable=False)
    decided_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    result = db.relationship("AllotmentResult")

    __table_args__ = (
        CheckConstraint("decision IN ('Accepted', 'Rejected')", name="ck_seat_decisions_decision"),
    )
