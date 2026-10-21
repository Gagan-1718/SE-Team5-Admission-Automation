"""Fictional eligibility cut-offs (safe to run repeatedly)."""
from sqlalchemy import select

from app.extensions import db

from .models import EligibilityRule

DEFAULT_RULES = (
    ("General", 20000),
    ("OBC", 30000),
    ("SC", 40000),
    ("ST", 40000),
    ("EWS", 25000),
)


def seed():
    """Create any missing rule. Existing rules are left untouched, so running twice adds nothing."""
    for category, max_rank in DEFAULT_RULES:
        exists = db.session.scalar(select(EligibilityRule).where(EligibilityRule.category == category))
        if exists is None:
            db.session.add(EligibilityRule(category=category, max_rank=max_rank, active=True))
    db.session.commit()
