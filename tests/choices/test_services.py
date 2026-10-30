"""Initial service contract checks for the choice-management implementation."""

from app.choices import services


def test_choice_error_types_expose_contract_status_codes():
    assert services.NotEligible.status_code == 403
    assert services.DuplicateChoice.status_code == 409
    assert services.ChoicesLocked.status_code == 409
    assert services.UnknownBranch.status_code == 404
    assert services.OrderMismatch.status_code == 400
    assert services.AlreadyLocked.status_code == 409
    assert services.NothingToLock.status_code == 422


def test_allotment_contract_functions_are_callable():
    assert callable(services.locked_candidate_ids)
    assert callable(services.get_locked_branch_ids)
