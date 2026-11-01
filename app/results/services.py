"""Result publication and seat decision services (owner: Dikshith).

Publication, private candidate views and one-time decisions use the shared schema.
A rejected seat is never released and the allotment is never rerun here.
"""

from sqlalchemy.exc import IntegrityError

from app.accounts.models import User
from app.accounts.services import get_exam_details
from app.allotment.services import get_completed_run, get_result_for_candidate
from app.allotment.models import AllotmentResult, ALLOCATED as ALLOCATION_STATUS
from app.choices.services import list_choices
from app.allotment.models import AllotmentRun
from app.audit.services import record_audit
from app.extensions import db
from .models import ResultPublication, SeatDecision, DECISIONS

NOT_PUBLISHED = "NOT_PUBLISHED"
NOT_IN_RUN = "NOT_IN_RUN"
NOT_ALLOCATED = "NOT_ALLOCATED"
ALLOCATED = "ALLOCATED"
VIEW_STATES = (NOT_PUBLISHED, NOT_IN_RUN, NOT_ALLOCATED, ALLOCATED)


class ResultError(Exception):
    status_code = 400


class RunNotFound(ResultError):
    status_code = 404


class AlreadyPublished(ResultError):
    status_code = 409


class NotPublished(ResultError):
    """Results are not published yet."""
    status_code = 404


class NotAllocated(ResultError):
    """The candidate has no seat to accept or reject (Not Allocated, or not in the run)."""
    status_code = 422


class AlreadyDecided(ResultError):
    status_code = 409


class InvalidDecision(ResultError):
    pass


def _decision_for_result(result_id):
    return db.session.execute(
        db.select(SeatDecision).where(SeatDecision.result_id == result_id)
    ).scalar_one_or_none()


def _decision_json(value):
    if value is None:
        return None
    return {"decision": value.decision, "decided_at": value.decided_at.isoformat()}



def publish(run_id, actor_id):
    """Publish a completed run. RunNotFound | AlreadyPublished."""
    actor = db.session.get(User, actor_id)
    if actor is None or actor.role != "administrator":
        raise PermissionError("Administrator access is required.")
    run = db.session.get(AllotmentRun, run_id)
    if run is None or run.completed_at is None:
        raise RunNotFound("No completed allotment run was found.")
    if is_published(run_id):
        raise AlreadyPublished("Results for this run have already been published.")

    publication = ResultPublication(run_id=run_id, published_by=actor_id)
    try:
        db.session.add(publication)
        # Flush first: the unique key chooses exactly one winner before any audit
        # entry is added. The publication and audit then share one commit.
        db.session.flush()
        record_audit(actor_id, "results.publish", target_type="allotment_run",
                     target_id=run_id, commit=False)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if is_published(run_id):
            raise AlreadyPublished(
                "Results for this run have already been published."
            ) from None
        raise
    except Exception:
        db.session.rollback()
        raise
    return publication


def is_published(run_id):
    """True once the run has been published (used by the administrator dashboard banner)."""
    return db.session.execute(
        db.select(ResultPublication.id).where(ResultPublication.run_id == run_id)
    ).scalar_one_or_none() is not None


def candidate_view(candidate_id):
    """{state: NOT_PUBLISHED | NOT_IN_RUN | NOT_ALLOCATED | ALLOCATED, result?, decision?}."""
    view = {"state": NOT_PUBLISHED, "result": None, "decision": None}
    run = get_completed_run()
    # Never load or serialize an allocation before this run is published.
    if run is None or run.completed_at is None or not is_published(run.id):
        return view
    result = get_result_for_candidate(candidate_id)
    if result is None or result.candidate_id != candidate_id or result.run_id != run.id:
        return {**view, "state": NOT_IN_RUN}
    summary = {
        "reference_number": result.reference_number,
        "status": result.status,
        "rank": result.rank,
        "category": result.category,
    }
    if result.status != ALLOCATION_STATUS:
        return {**view, "state": NOT_ALLOCATED, "result": summary}
    user = db.session.get(User, candidate_id)
    exam = get_exam_details(candidate_id) or {}
    summary.update(
        candidate_name=user.name if user else "Candidate",
        college=result.branch.college.name,
        branch=result.branch.name,
        choice_priority=result.choice_priority,
        total_choices=len(list_choices(candidate_id)),
        exam_type=exam.get("exam_type"),
    )
    return {"state": ALLOCATED, "result": summary,
            "decision": _decision_json(_decision_for_result(result.id))}


def decide(candidate_id, decision):
    """Record 'Accepted' or 'Rejected' once. NotPublished | NotAllocated | AlreadyDecided."""
    actor = db.session.get(User, candidate_id)
    if actor is None or actor.role != "candidate":
        raise PermissionError("Only candidates can record a seat decision.")
    view = candidate_view(candidate_id)
    if view["state"] == NOT_PUBLISHED:
        raise NotPublished("Results have not been published yet.")
    if view["state"] != ALLOCATED:
        raise NotAllocated("You do not have an allocated seat to accept or reject.")
    if not isinstance(decision, str) or decision not in DECISIONS:
        raise InvalidDecision("Choose Accept or Reject.")
    if view["decision"] is not None:
        raise AlreadyDecided("Your decision has already been recorded")
    result = get_result_for_candidate(candidate_id)
    value = SeatDecision(result_id=result.id, decision=decision)
    try:
        db.session.add(value)
        # The unique result_id key arbitrates simultaneous requests. Only its
        # winner writes an audit event, in the same transaction as the decision.
        db.session.flush()
        record_audit(candidate_id, "results.decision", target_type="allotment_result",
                     target_id=result.id, actor_role="candidate", commit=False)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if _decision_for_result(result.id) is not None:
            raise AlreadyDecided("Your decision has already been recorded") from None
        raise
    except Exception:
        db.session.rollback()
        raise
    return value


def publication_details(run_id):
    """Display metadata owned by Results, for the administrator console."""
    publication = db.session.execute(
        db.select(ResultPublication).where(ResultPublication.run_id == run_id)
    ).scalar_one_or_none()
    if publication is None:
        return None
    publisher = db.session.get(User, publication.published_by)
    return {
        "published_at": publication.published_at,
        "published_by": publication.published_by,
        "publisher_name": publisher.name if publisher else "Administrator",
    }


def decision_summary(run_id):
    """Counts for the console: only allocated seats need a decision."""
    counts = {"Accepted": 0, "Rejected": 0, "Undecided": 0}
    rows = db.session.execute(
        db.select(SeatDecision.decision, db.func.count(AllotmentResult.id))
        .select_from(AllotmentResult)
        .outerjoin(SeatDecision, SeatDecision.result_id == AllotmentResult.id)
        .where(AllotmentResult.run_id == run_id, AllotmentResult.status == ALLOCATION_STATUS)
        .group_by(SeatDecision.decision)
    ).all()
    for decision, count in rows:
        counts[decision or "Undecided"] = count
    return counts
