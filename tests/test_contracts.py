"""The Sprint Two contracts (SPRINT_TWO_START_HERE.md section 4).

These tests fail if someone renames an agreed function, drops an agreed parameter, changes the
HTTP status an agreed error stands for, or breaks the journey step shape. Owners may add
optional parameters after the agreed ones and may replace stub bodies; nothing else.
"""
import importlib
import inspect

import pytest

from app import MODULES
from app.allotment.models import AllotmentResult, AllotmentRun
from app.journey import JOURNEY_KEYS, STATES, all_steps, make_step

# module -> function -> the agreed leading parameters
FUNCTIONS = {
    "app.choices.services": {
        "list_choices": ["candidate_id"],
        "add_choice": ["candidate_id", "branch_id"],
        "remove_choice": ["candidate_id", "choice_id"],
        "reorder": ["candidate_id", "ordered_choice_ids"],
        "lock": ["candidate_id"],
        "is_locked": ["candidate_id"],
        "locked_candidate_ids": [],
        "get_locked_branch_ids": ["candidate_id"],
    },
    "app.allotment.engine": {"allot": ["candidates", "seats"]},
    "app.allotment.services": {
        "run_allotment": ["actor_id"],
        "get_completed_run": [],
        "get_result_for_candidate": ["candidate_id"],
        "seat_consistency_report": [],
    },
    "app.results.services": {
        "publish": ["run_id", "actor_id"],
        "is_published": ["run_id"],
        "candidate_view": ["candidate_id"],
        "decide": ["candidate_id", "decision"],
    },
    "app.audit.services": {
        "record_audit": ["actor_id", "action_type", "target_type", "target_id", "outcome", "actor_role", "commit"],
        "record_admin_action": ["action_type", "target_type", "target_id", "outcome", "commit"],
    },
}

# module -> error class -> the HTTP status it stands for
ERRORS = {
    "app.choices.services": {
        "NotEligible": 403, "DuplicateChoice": 409, "ChoicesLocked": 409, "UnknownBranch": 404,
        "OrderMismatch": 400, "AlreadyLocked": 409, "NothingToLock": 422,
    },
    "app.allotment.services": {"AlreadyCompleted": 409, "NothingToAllot": 422, "RunFailed": 500},
    "app.results.services": {
        "RunNotFound": 404, "AlreadyPublished": 409, "NotPublished": 404,
        "NotAllocated": 422, "AlreadyDecided": 409,
    },
}


def test_new_modules_are_registered_before_audit_and_admin():
    order = list(MODULES)
    for name in ("choices", "allotment", "results"):
        assert order.index("eligibility") < order.index(name) < order.index("audit")
    assert order[-2:] == ["audit", "admin"]


@pytest.mark.parametrize(
    ("module_name", "function_name", "agreed"),
    [(m, f, p) for m, funcs in FUNCTIONS.items() for f, p in funcs.items()],
)
def test_agreed_function_exists_with_agreed_parameters(module_name, function_name, agreed):
    function = getattr(importlib.import_module(module_name), function_name)
    parameters = list(inspect.signature(function).parameters)
    assert parameters[: len(agreed)] == agreed


@pytest.mark.parametrize(
    ("module_name", "error_name", "status"),
    [(m, e, s) for m, errors in ERRORS.items() for e, s in errors.items()],
)
def test_agreed_error_exists_with_agreed_status(module_name, error_name, status):
    error = getattr(importlib.import_module(module_name), error_name)
    assert issubclass(error, Exception)
    assert error.status_code == status


def test_audit_flag_defaults_to_committing():
    """Existing callers keep committing; only the allotment run passes commit=False."""
    from app.audit.services import record_admin_action, record_audit

    assert inspect.signature(record_audit).parameters["commit"].default is True
    assert inspect.signature(record_admin_action).parameters["commit"].default is True


def test_journey_returns_the_seven_steps_in_order(app):
    steps = all_steps(candidate_id=1)
    assert [step["key"] for step in steps] == list(JOURNEY_KEYS)
    for step in steps:
        assert set(step) == {"key", "label", "state", "detail", "href"}
        assert step["state"] in STATES
        assert step["href"].startswith("/")


def test_make_step_refuses_an_unknown_state():
    with pytest.raises(ValueError):
        make_step("documents", "Documents", "almost-done", "x", "/documents")


def test_no_run_and_no_result_before_allotment(app):
    from app.allotment.services import get_completed_run, get_result_for_candidate

    assert get_completed_run() is None
    assert get_result_for_candidate(1) is None


def test_result_lookups_find_the_completed_run_and_the_candidates_row(app):
    from app.accounts.models import User
    from app.allotment.services import get_completed_run, get_result_for_candidate
    from app.catalogue.models import Branch, Seat
    from app.catalogue.seed import seed as seed_catalogue
    from app.extensions import db

    admin = User(name="Fictional Admin", email="contract.admin@example.test", mobile="9400000001",
                 password_hash="not-a-real-hash", role="administrator")
    candidate = User(name="Fictional Candidate", email="contract.cand@example.test", mobile="9400000002",
                     password_hash="not-a-real-hash", role="candidate")
    other = User(name="Fictional Other", email="contract.other@example.test", mobile="9400000003",
                 password_hash="not-a-real-hash", role="candidate")
    db.session.add_all([admin, candidate, other])
    seed_catalogue()
    db.session.commit()
    branch = db.session.execute(db.select(Branch).order_by(Branch.id)).scalars().first()
    seat = db.session.execute(db.select(Seat).filter_by(branch_id=branch.id)).scalars().first()
    run = AllotmentRun(run_by=admin.id, candidates_processed=1, allocated_count=1, not_allocated_count=0)
    db.session.add(run)
    db.session.commit()
    db.session.add(AllotmentResult(run_id=run.id, candidate_id=candidate.id, rank=1, category="General",
                                   reference_number="ADM-2026-000001", status="Allocated",
                                   branch_id=branch.id, seat_id=seat.id, choice_priority=1))
    db.session.commit()

    assert get_completed_run().id == run.id
    assert get_result_for_candidate(candidate.id).branch_id == branch.id
    assert get_result_for_candidate(other.id) is None  # not part of the run, not "Not Allocated"
