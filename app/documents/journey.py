"""Journey step for the candidate dashboard (SPRINT_TWO_START_HERE.md section 4.4)."""
from app.application.services import get_for_candidate
from app.extensions import db
from app.journey import CURRENT, DONE, LOCKED, PROBLEM, WAITING, make_step

from .models import Document
from .services import REQUIRED_DOCUMENT_TYPES

KEY, LABEL, HREF = "documents", "Documents", "/documents"


def step_statuses(candidate_id):
    application = get_for_candidate(candidate_id)
    if application is None or application.is_draft:
        return [make_step(KEY, LABEL, LOCKED, "Submit your application first.", HREF)]

    rows = db.session.execute(
        db.select(Document.document_type, Document.status, Document.rejection_reason).where(
            Document.candidate_id == candidate_id,
            Document.document_type.in_(REQUIRED_DOCUMENT_TYPES),
        )
    ).all()
    by_type = {}
    for document_type, status, reason in rows:
        by_type.setdefault(document_type, []).append((status, reason))

    rejected = [(t, reason) for t, docs in by_type.items() for status, reason in docs if status == "Rejected"]
    if rejected:
        document_type, reason = rejected[0]
        detail = f"{document_type} was rejected: {reason}. Upload a corrected file." if reason \
            else f"{document_type} was rejected. Upload a corrected file."
        return [make_step(KEY, LABEL, PROBLEM, detail, HREF)]

    missing = [t for t in REQUIRED_DOCUMENT_TYPES if t not in by_type]
    if missing:
        return [make_step(KEY, LABEL, CURRENT, "Upload " + ", ".join(missing) + ".", HREF)]

    approved = sum(all(status == "Approved" for status, _ in docs) for docs in by_type.values())
    total = len(REQUIRED_DOCUMENT_TYPES)
    if approved < total:
        return [make_step(KEY, LABEL, WAITING,
                          f"Waiting for administrator review ({approved} of {total} approved).", HREF)]
    return [make_step(KEY, LABEL, DONE, f"All {total} required documents approved.", HREF)]
