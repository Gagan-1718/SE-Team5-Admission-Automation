import pytest

from app.choices import services
from app.choices.services import add_choice, get_locked_branch_ids, lock


@pytest.fixture
def eligible(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "fictional test eligibility"
    })


def test_locked_candidate_contracts_return_exact_ids_in_priority_order(app, choice_data, eligible):
    first_candidate, second_candidate = choice_data["candidate_ids"]
    first_branch, second_branch = choice_data["branch_ids"][:2]
    with app.app_context():
        add_choice(first_candidate, first_branch)
        second = add_choice(first_candidate, second_branch)
        lock(first_candidate)

        assert services.locked_candidate_ids() == [first_candidate]
        assert get_locked_branch_ids(first_candidate) == [first_branch, second_branch]
        assert get_locked_branch_ids(second_candidate) == []


def test_unlocked_candidates_are_excluded_from_both_contracts(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    with app.app_context():
        add_choice(candidate_id, choice_data["branch_ids"][0])
        assert candidate_id not in services.locked_candidate_ids()
        assert services.get_locked_branch_ids(candidate_id) == []
