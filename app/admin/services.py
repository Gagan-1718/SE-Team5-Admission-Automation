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
        db.select(Document, User.name, Application.reference_number)
        .join(User, User.id == Document.candidate_id)
        .outerjoin(Application, Application.id == Document.application_id)
        .where(Document.status == "Pending").order_by(Document.id.desc())
    ).all()
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
            {"id": d.id, "candidateId": d.candidate_id, "documentType": d.document_type,
             "candidateName": name, "referenceNumber": reference}
            for d, name, reference in pending
        ],
    }


def _split(*parts):
    """[(label, count, tone)] with each part's share of the whole, for segmented bars."""
    total = sum(count for _, count, _ in parts)
    return {"total": total, "parts": [
        {"label": label, "count": count, "tone": tone, "percent": round(count * 100 / total, 1) if total else 0}
        for label, count, tone in parts]}


def cycle_overview():
    """Whole-cycle figures for the dashboard, including every negative outcome (ADM-F-020)."""
    from app.allotment.models import ALLOCATED, AllotmentResult
    from app.allotment.services import get_completed_run
    from app.catalogue.models import Branch, College, Seat
    from app.choices.models import Choice, ChoiceLock
    from app.documents.services import REQUIRED_DOCUMENT_TYPES
    from app.eligibility.evaluation import ELIGIBLE, NOT_ELIGIBLE, evaluate_eligibility
    from app.eligibility.models import EligibilityRule
    from app.results.models import SeatDecision
    from app.results.services import is_published

    candidates = db.session.execute(
        db.select(User).where(User.role == "candidate")).scalars().all()
    applications = dict(db.session.execute(db.select(Application.candidate_id, Application.status)).all())
    approved_types = db.session.execute(
        db.select(Document.candidate_id, func.count(func.distinct(Document.document_type)))
        .where(Document.status == "Approved", Document.document_type.in_(REQUIRED_DOCUMENT_TYPES))
        .group_by(Document.candidate_id)).all()
    all_approved = {cid for cid, n in approved_types if n == len(REQUIRED_DOCUMENT_TYPES)}
    rules = db.session.scalars(db.select(EligibilityRule)).all()
    locked = set(db.session.scalars(db.select(ChoiceLock.candidate_id)))
    with_choices = set(db.session.scalars(db.select(Choice.candidate_id).distinct()))

    status_of = {}
    for user in candidates:
        if user.exam_record is None:
            status_of[user.id] = "Pending"
        else:
            status_of[user.id] = evaluate_eligibility(
                user.exam_record.rank, user.exam_record.category, user.id in all_approved, rules)["status"]
    eligible = {cid for cid, s in status_of.items() if s == ELIGIBLE}
    submitted = {cid for cid, s in applications.items() if s == "Submitted"}
    documents = _count_by(Document.status, DOCUMENT_STATUSES)

    run = get_completed_run()
    published = bool(run and is_published(run.id))
    allocated = not_allocated = accepted = rejected_seats = 0
    if run:
        results = dict(db.session.execute(
            db.select(AllotmentResult.status, func.count()).where(AllotmentResult.run_id == run.id)
            .group_by(AllotmentResult.status)).all())
        allocated = results.get(ALLOCATED, 0)
        not_allocated = sum(results.values()) - allocated
        decisions = dict(db.session.execute(
            db.select(SeatDecision.decision, func.count())
            .join(AllotmentResult, AllotmentResult.id == SeatDecision.result_id)
            .where(AllotmentResult.run_id == run.id).group_by(SeatDecision.decision)).all())
        accepted, rejected_seats = decisions.get("Accepted", 0), decisions.get("Rejected", 0)

    total = len(candidates)
    pipeline = [
        ("Registered", total),
        ("Exam details entered", sum(1 for u in candidates if u.exam_record is not None)),
        ("Application submitted", len(submitted)),
        ("All documents approved", len(all_approved)),
        ("Eligible", len(eligible)),
        ("Choices locked", len(eligible & locked)),
        ("Seat allotted", allocated),
        ("Seat accepted", accepted),
    ]
    seats = db.session.execute(
        db.select(College.name, func.sum(Seat.filled), func.sum(Seat.capacity))
        .join(Branch, Branch.college_id == College.id).join(Seat, Seat.branch_id == Branch.id)
        .group_by(College.name).order_by(func.sum(Seat.capacity).desc())).all()

    return {
        "total": total,
        "pipeline": [{"label": label, "count": count,
                      "percent": round(count * 100 / total, 1) if total else 0} for label, count in pipeline],
        "applications": _split(("Submitted", len(submitted), "ok"),
                               ("Draft", sum(1 for s in applications.values() if s == "Draft"), "wait"),
                               ("Not started", total - len(applications), "idle")),
        "documents": _split(("Approved", documents["Approved"], "ok"), ("Pending", documents["Pending"], "wait"),
                            ("Rejected", documents["Rejected"], "bad")),
        "eligibility": _split(("Eligible", len(eligible), "ok"),
                              ("Pending", sum(1 for s in status_of.values() if s == "Pending"), "wait"),
                              ("Not eligible", sum(1 for s in status_of.values() if s == NOT_ELIGIBLE), "bad")),
        "choices": _split(("Locked", len(eligible & locked), "ok"),
                          ("Saved, not locked", len((eligible & with_choices) - locked), "wait"),
                          ("No choices yet", len(eligible - with_choices - locked), "idle")),
        "allotment": _split(("Allocated", allocated, "ok"), ("Not allocated", not_allocated, "bad"),
                            ("Not in the run", total - allocated - not_allocated, "idle")) if run else None,
        "decisions": _split(("Accepted", accepted, "ok"), ("Undecided", allocated - accepted - rejected_seats, "wait"),
                            ("Rejected", rejected_seats, "bad")) if run else None,
        "seats": [{"college": name, "filled": int(filled or 0), "capacity": int(cap or 0)} for name, filled, cap in seats],
        "run": run,
        "published": published,
    }
