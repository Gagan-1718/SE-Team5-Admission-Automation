"""Result publication and seat decision services (owner: Dikshith).

Publication is implemented for issue #12. Candidate views and decisions remain
contract stubs for the next small PRs. Shared names and schemas are unchanged.
"""

from sqlalchemy.exc import IntegrityError

from app.accounts.models import User
from app.allotment.models import AllotmentRun
from app.audit.services import record_audit
from app.extensions import db
from .models import ResultPublication

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


def _todo(issue):
    raise NotImplementedError(f"Contract stub: implement in issue {issue}.")


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
    _todo("#13")


def decide(candidate_id, decision):
    """Record 'Accepted' or 'Rejected' once. NotPublished | NotAllocated | AlreadyDecided."""
    _todo("#14")


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
