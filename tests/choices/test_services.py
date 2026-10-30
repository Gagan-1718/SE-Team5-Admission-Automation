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
    assert services.ChoiceNotFound.status_code == 404


def test_allotment_contract_functions_are_callable():
    assert callable(services.locked_candidate_ids)
    assert callable(services.get_locked_branch_ids)


def test_choice_errors_have_safe_client_messages():
    assert str(services.DuplicateChoice()) == "That branch is already in your list."
    assert str(services.NothingToLock()) == "Add at least one choice first"
    assert str(services.ChoiceNotFound()) == "That choice was not found."


def test_mutation_guard_rejects_non_eligible_candidates(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Pending", "reason": "Documents are under review."
    })
    try:
        services._require_eligible(1)
    except services.NotEligible as exc:
        assert str(exc) == "Documents are under review."
    else:
        raise AssertionError("pending candidate was not rejected")


def test_mutation_guard_accepts_only_eligible_candidates(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Not Eligible", "reason": "Rank is outside the cut-off."
    })
    try:
        services._require_eligible(2)
    except services.NotEligible:
        pass
    else:
        raise AssertionError("not-eligible candidate was not rejected")

    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "Rank is within the cut-off."
    })
    assert services._require_eligible(2)["status"] == "Eligible"
