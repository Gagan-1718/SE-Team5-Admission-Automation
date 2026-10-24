"""Read-only numbers for the administrator dashboard (ADM-F-020).

Reads the accounts, application and documents tables; changes nothing.
"""
from sqlalchemy import func

from app.accounts.models import User
from app.application.models import Application
from app.documents.models import Document
from app.extensions import db

APPLICATION_STATUSES = ("Draft", "Submitted")
DOCUMENT_STATUSES = ("Pending", "Approved", "Rejected")


def _count_by(column, wanted, *where):
    stmt = db.select(column, func.count()).group_by(column)
    for clause in where:
        stmt = stmt.where(clause)
    found = dict(db.session.execute(stmt).all())
    return {name: int(found.get(name, 0)) for name in wanted}


def dashboard_summary():
    candidates = db.session.scalar(
        db.select(func.count()).select_from(User).where(User.role == "candidate")
    )
    with_exam = db.session.scalar(
        db.select(func.count()).select_from(User).where(
            User.role == "candidate", User.exam_record_id.is_not(None)
        )
    )
    pending = db.session.execute(
        db.select(Document).where(Document.status == "Pending").order_by(Document.id)
    ).scalars().all()
    return {
        "candidateCounts": {
            "total": int(candidates),
            "withExamDetails": int(with_exam),
        },
        "statusCounts": {
            "applications": _count_by(Application.status, APPLICATION_STATUSES),
            "documents": _count_by(Document.status, DOCUMENT_STATUSES),
        },
        "pendingDocuments": [
            {"id": d.id, "candidateId": d.candidate_id, "documentType": d.document_type}
            for d in pending
        ],
    }
