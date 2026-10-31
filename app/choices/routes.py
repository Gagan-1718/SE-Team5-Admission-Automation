"""Candidate choice-management JSON API (Issues #21, #22 and #23)."""

from flask import Blueprint, jsonify, request

from app.accounts.auth import current_candidate_id, role_required
from app.catalogue.models import Branch
from app.extensions import db
from .models import ChoiceLock

from .services import (
    ChoiceError,
    InvalidChoiceRequest,
    add_choice,
    is_locked,
    list_choices,
    lock,
    preview_choice,
    remove_choice,
    reorder,
)

bp = Blueprint("choices", __name__)


def _error(exc):
    return jsonify(status=exc.status_code, error=type(exc).__name__, message=str(exc)), exc.status_code


def _body():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise InvalidChoiceRequest("A JSON object is required.")
    return payload


def _integer(payload, key):
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidChoiceRequest(f"{key} must be an integer.")
    return value


def _serialized(candidate_id):
    return [preview_choice(choice, candidate_id) for choice in list_choices(candidate_id)]


@bp.get("/api/v1/choices")
@role_required("candidate")
def choices_list():
    candidate_id = current_candidate_id()
    return jsonify(choices=_serialized(candidate_id), locked=is_locked(candidate_id))


@bp.post("/api/v1/choices")
@role_required("candidate")
def choices_add():
    candidate_id = current_candidate_id()
    try:
        payload = _body()
        branch_id = _integer(payload, "branchId")
        if "collegeId" in payload:
            college_id = _integer(payload, "collegeId")
            branch = db.session.get(Branch, branch_id)
            if branch is None or branch.college_id != college_id:
                from .services import UnknownBranch
                raise UnknownBranch("The branch does not belong to the selected college.")
        choice = add_choice(candidate_id, branch_id)
        return jsonify(choice=preview_choice(choice, candidate_id), locked=False), 201
    except ChoiceError as exc:
        return _error(exc)


@bp.delete("/api/v1/choices/<int:choice_id>")
@role_required("candidate")
def choices_remove(choice_id):
    candidate_id = current_candidate_id()
    try:
        remove_choice(candidate_id, choice_id)
        return jsonify(choices=_serialized(candidate_id), locked=False)
    except ChoiceError as exc:
        return _error(exc)


@bp.put("/api/v1/choices/order")
@role_required("candidate")
def choices_reorder():
    candidate_id = current_candidate_id()
    try:
        payload = _body()
        order = payload.get("orderedChoiceIds")
        if not isinstance(order, list) or any(isinstance(value, bool) or not isinstance(value, int) for value in order):
            raise InvalidChoiceRequest("orderedChoiceIds must be a list of integers.")
        reorder(candidate_id, order)
        return jsonify(choices=_serialized(candidate_id), locked=False)
    except ChoiceError as exc:
        return _error(exc)


@bp.post("/api/v1/choices/lock")
@role_required("candidate")
def choices_lock():
    candidate_id = current_candidate_id()
    try:
        lock(candidate_id)
        row = db.session.get(ChoiceLock, candidate_id)
        return jsonify(locked=True, lockedAt=row.locked_at.isoformat())
    except ChoiceError as exc:
        return _error(exc)
