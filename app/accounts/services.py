"""Read-only services exposed to other application modules."""

from app.extensions import db

from .models import User


def get_exam_details(candidate_id):
    """Return stored exam details for a candidate, or None when not entered."""
    user = db.session.get(User, candidate_id)
    if not user or not user.exam_record:
        return None
    record = user.exam_record
    return {
        "exam_type": record.exam_type,
        "rank": record.rank,
        "category": record.category,
        "score": record.score,
    }
