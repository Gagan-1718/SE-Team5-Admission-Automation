"""Eligibility service: other modules call get_eligibility(candidate_id)."""
from sqlalchemy import select

from app.accounts.services import get_exam_details
from app.documents.services import all_documents_approved
from app.extensions import db

from .evaluation import PENDING, evaluate_eligibility
from .models import EligibilityRule

__all__ = ["ExamDetailsNotEntered", "evaluate_eligibility", "get_eligibility"]


class ExamDetailsNotEntered(LookupError):
    """The candidate has not entered exam details yet (SAD: 422 exam details not entered)."""


def get_eligibility(candidate_id, require_exam_details=False):
    """Return {'status': 'Pending'|'Eligible'|'Not Eligible', 'reason': str}.

    Without exam details the default answer is Pending. The JSON endpoint passes
    require_exam_details=True to get ExamDetailsNotEntered instead.
    """
    details = get_exam_details(candidate_id)
    if details is None:
        if require_exam_details:
            raise ExamDetailsNotEntered("exam details not entered")
        return {"status": PENDING, "reason": "Exam details have not been entered yet."}
    rules = db.session.scalars(select(EligibilityRule)).all()
    return evaluate_eligibility(
        details["rank"], details["category"], all_documents_approved(candidate_id), rules
    )
