"""Smoke-test table that proves the SQLite connection can save and read a record.

Owned by the shared foundation (#31). It holds fictional text only and can be
removed once real modules exercise the database in their own tests.
"""
from datetime import datetime, timezone

from .extensions import db


class SetupCheck(db.Model):
    __tablename__ = "setup_check"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(80), nullable=False, unique=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )


FICTIONAL_LABEL = "fictional setup record"


def seed():
    """Create the fictional record if it is missing (safe to run repeatedly)."""
    exists = db.session.execute(
        db.select(SetupCheck).filter_by(label=FICTIONAL_LABEL)
    ).scalar_one_or_none()
    if exists is None:
        db.session.add(SetupCheck(label=FICTIONAL_LABEL))
        db.session.commit()
