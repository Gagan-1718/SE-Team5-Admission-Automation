"""Eligibility service: other modules call get_eligibility(candidate_id)."""
from sqlalchemy import select

from app.extensions import db

from .evaluation import evaluate_eligibility
from .models import EligibilityRule

__all__ = ["evaluate_eligibility", "get_eligibility"]


def _temporary_inputs(candidate_id):
    """TEMPORARY (Day 2): fixed sample inputs so this module works on its own.

    Day 3 replacement: rank and category come from
    app.accounts.services.get_exam_details(candidate_id) and documents_approved from
    app.documents.services.all_documents_approved(candidate_id). Delete this function then.
    """
    return {"rank": 1000, "category": "General", "documents_approved": True}


def get_eligibility(candidate_id):
    """Return {'status': 'Pending'|'Eligible'|'Not Eligible', 'reason': str}."""
    inputs = _temporary_inputs(candidate_id)
    rules = db.session.scalars(select(EligibilityRule)).all()
    return evaluate_eligibility(
        inputs["rank"], inputs["category"], inputs["documents_approved"], rules
    )
