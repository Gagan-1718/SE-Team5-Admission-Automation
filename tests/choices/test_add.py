import pytest

from app.choices import services
from app.choices.services import add_choice
from app.extensions import db


@pytest.fixture
def eligible(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "fictional test eligibility"
    })


def test_eligible_candidate_adds_choices_in_next_priority(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    first_id, second_id = choice_data["branch_ids"][:2]
    with app.app_context():
        first = add_choice(candidate_id, first_id)
        second = add_choice(candidate_id, second_id)
        assert (first.priority, second.priority) == (1, 2)
        assert [row.branch_id for row in services.list_choices(candidate_id)] == [first_id, second_id]


def test_unknown_branch_is_rejected_without_a_row(app, choice_data, eligible):
    with app.app_context():
        with pytest.raises(services.UnknownBranch):
            add_choice(choice_data["candidate_ids"][0], 999999)
        assert db.session.query(services.Choice).count() == 0


def test_duplicate_branch_is_rejected(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    branch_id = choice_data["branch_ids"][0]
    with app.app_context():
        add_choice(candidate_id, branch_id)
        with pytest.raises(services.DuplicateChoice):
            add_choice(candidate_id, branch_id)


def test_pending_candidate_cannot_add(app, choice_data, monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Pending", "reason": "Documents are under review."
    })
    with app.app_context():
        with pytest.raises(services.NotEligible):
            add_choice(choice_data["candidate_ids"][0], choice_data["branch_ids"][0])
