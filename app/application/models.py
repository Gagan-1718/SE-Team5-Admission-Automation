"""Application model (owner: Gagan).

Shared contract fields: id, candidate_id, status, reference_number.
Statuses: Draft and Submitted. The other columns are the draft form fields.
"""
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from app.extensions import db

DRAFT = "Draft"
SUBMITTED = "Submitted"
STATUSES = (DRAFT, SUBMITTED)

# Editable form fields. Provisional list - to be confirmed with the team (SRS has no field list).
FORM_FIELDS = ("guardian_name", "guardian_mobile", "school_name", "board", "percentage")


def _now():
    return datetime.now(timezone.utc)


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    # One application per candidate. No foreign key yet: the users table belongs to
    # the accounts module (Varun). Add REFERENCES users(id) when login is integrated.
    candidate_id = db.Column(db.Integer, nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default=DRAFT)
    reference_number = db.Column(db.String(30), unique=True)  # set only on submission (#3)

    guardian_name = db.Column(db.String(100))
    guardian_mobile = db.Column(db.String(10))
    school_name = db.Column(db.String(150))
    board = db.Column(db.String(40))
    percentage = db.Column(db.Float)

    created_at = db.Column(db.DateTime, nullable=False, default=_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Submitted')", name="ck_applications_status"),
        CheckConstraint(
            "percentage IS NULL OR (percentage >= 0 AND percentage <= 100)",
            name="ck_applications_percentage",
        ),
    )

    @property
    def is_draft(self):
        return self.status == DRAFT

    def fields(self):
        return {name: getattr(self, name) for name in FORM_FIELDS}
