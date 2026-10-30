"""Choice list services (owner: Varun).

CONTRACT STUBS: names, parameters and error types are agreed in SPRINT_TWO_START_HERE.md
section 4.3. Varun replaces the bodies (issues #21, #22, #23); do not rename anything.
Each error carries the HTTP status the routes should use.
"""

from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.accounts.services import get_exam_details
from app.eligibility.services import get_eligibility
from app.extensions import db
from app.catalogue.models import Branch

from .models import Choice, ChoiceLock


ERROR_MESSAGES = {
    "NotEligible": "Choices are available only after eligibility is confirmed.",
    "DuplicateChoice": "That branch is already in your list.",
    "ChoicesLocked": "Your choices are locked and cannot be changed.",
    "UnknownBranch": "The selected branch was not found.",
    "OrderMismatch": "The submitted order must contain exactly your current choices.",
    "AlreadyLocked": "Your choices are already locked.",
    "NothingToLock": "Add at least one choice first",
    "ChoiceNotFound": "That choice was not found.",
}


class ChoiceError(Exception):
    status_code = 400

    def __init__(self, message=None):
        super().__init__(message or ERROR_MESSAGES.get(type(self).__name__, "Choice operation failed."))


class NotEligible(ChoiceError):
    """The candidate is not Eligible, so they cannot add choices."""
    status_code = 403


class DuplicateChoice(ChoiceError):
    """That branch is already in the candidate's list."""
    status_code = 409


class ChoicesLocked(ChoiceError):
    """The list is locked: no add, remove or reorder."""
    status_code = 409


class UnknownBranch(ChoiceError):
    """No such branch in the catalogue."""
    status_code = 404


class OrderMismatch(ChoiceError):
    """The ids sent for reordering are not exactly the candidate's current choices."""
    status_code = 400


class AlreadyLocked(ChoiceError):
    status_code = 409


class NothingToLock(ChoiceError):
    """Locking needs at least one choice."""
    status_code = 422


class ChoiceNotFound(ChoiceError):
    """The requested choice does not exist for the candidate."""

    status_code = 404


def _todo(issue):
    raise NotImplementedError(f"Contract stub: implement in issue {issue}.")


def list_choices(candidate_id):
    """The candidate's Choice rows ordered by priority."""
    return list(
        db.session.scalars(
            db.select(Choice)
            .where(Choice.candidate_id == candidate_id)
            .options(selectinload(Choice.branch).selectinload(Branch.college),
                     selectinload(Choice.branch).selectinload(Branch.seats))
            .order_by(Choice.priority, Choice.id)
        ).all()
    )


def preview_choice(choice, candidate_id):
    """Return frontend-safe display data for one loaded choice."""
    details = get_exam_details(candidate_id) or {}
    category = details.get("category")
    seat = choice.branch.seat_for(category) if category else None
    return {
        "id": choice.id,
        "priority": choice.priority,
        "college": choice.branch.college.name,
        "city": choice.branch.college.city,
        "branch": choice.branch.name,
        "branchId": choice.branch_id,
        "collegeId": choice.branch.college_id,
        "category": category,
        "seatsAvailable": seat.available if seat else 0,
        "seatCapacity": seat.capacity if seat else 0,
    }


def _require_eligible(candidate_id):
    """Reject pending and ineligible candidates using the shared eligibility service."""
    result = get_eligibility(candidate_id)
    if result.get("status") != "Eligible":
        raise NotEligible(result.get("reason") or ERROR_MESSAGES["NotEligible"])
    return result


def _require_unlocked(candidate_id):
    """Reject every mutation after the permanent lock row exists."""
    if is_locked(candidate_id):
        raise ChoicesLocked()


def add_choice(candidate_id, branch_id):
    """Add a branch at the next priority. NotEligible | DuplicateChoice | ChoicesLocked | UnknownBranch."""
    _require_eligible(candidate_id)
    _require_unlocked(candidate_id)
    branch = db.session.get(Branch, branch_id)
    if branch is None:
        raise UnknownBranch()
    duplicate = db.session.scalar(
        db.select(Choice.id).where(
            Choice.candidate_id == candidate_id, Choice.branch_id == branch_id
        )
    )
    if duplicate is not None:
        raise DuplicateChoice()
    last_priority = db.session.scalar(
        db.select(db.func.max(Choice.priority)).where(Choice.candidate_id == candidate_id)
    ) or 0
    choice = Choice(candidate_id=candidate_id, branch_id=branch_id, priority=last_priority + 1)
    db.session.add(choice)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if is_locked(candidate_id):
            raise ChoicesLocked() from None
        raise DuplicateChoice() from None
    return choice


def remove_choice(candidate_id, choice_id):
    """Remove a choice and renumber. ChoicesLocked."""
    _todo("#21")


def reorder(candidate_id, ordered_choice_ids):
    """Save a new order; returns the list. ChoicesLocked | OrderMismatch."""
    _todo("#22")


def lock(candidate_id):
    """Lock the list for ever. AlreadyLocked | NothingToLock."""
    _todo("#23")


def is_locked(candidate_id):
    return db.session.get(ChoiceLock, candidate_id) is not None


def locked_candidate_ids():
    """Ids of every candidate who has locked their list (used by the allotment run)."""
    _todo("#23")


def get_locked_branch_ids(candidate_id):
    """Branch ids in priority order for a locked list; [] when the list is not locked."""
    _todo("#23")
