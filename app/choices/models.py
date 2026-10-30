"""Choice list tables (owner: Varun). Shape agreed in SPRINT_TWO_START_HERE.md section 4.2.

``choices`` holds one row per college-branch pair a candidate wants; priority 1 is the most
preferred and priorities are kept as 1..n with no gaps by the service. A candidate's list is
open until a ``choice_locks`` row exists for them; there is no way to remove that row.
"""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db


def _now():
    return datetime.now(timezone.utc)


class Choice(db.Model):
    __tablename__ = "choices"

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey("catalogue_branch.id"), nullable=False, index=True)
    priority = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)

    branch = db.relationship("Branch")

    __table_args__ = (
        # No duplicates: the database refuses the same branch twice for one candidate.
        UniqueConstraint("candidate_id", "branch_id", name="uq_choices_candidate_branch"),
        CheckConstraint("priority >= 1", name="ck_choices_priority_positive"),
    )


class ChoiceLock(db.Model):
    """Exists exactly when the candidate has locked their list (ADM-F-014)."""

    __tablename__ = "choice_locks"

    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    locked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
