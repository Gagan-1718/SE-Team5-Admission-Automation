import pytest

from app.choices import services
from app.choices.services import add_choice, remove_choice


@pytest.fixture
def eligible(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "fictional test eligibility"
    })


def test_candidate_removes_own_choice_and_remaining_priorities_are_contiguous(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    first_id, second_id, third_id = choice_data["branch_ids"]
    with app.app_context():
        first = add_choice(candidate_id, first_id)
        add_choice(candidate_id, second_id)
        third = add_choice(candidate_id, third_id)
        remaining = remove_choice(candidate_id, first.id)
        assert [row.branch_id for row in remaining] == [second_id, third_id]
        assert [row.priority for row in remaining] == [1, 2]


def test_candidate_cannot_remove_another_candidates_choice(app, choice_data, eligible):
    first_candidate, second_candidate = choice_data["candidate_ids"]
    branch_id = choice_data["branch_ids"][0]
    with app.app_context():
        foreign = add_choice(second_candidate, branch_id)
        with pytest.raises(services.ChoiceNotFound):
            remove_choice(first_candidate, foreign.id)
        assert services.list_choices(second_candidate)[0].id == foreign.id


def test_unknown_choice_is_handled_without_changes(app, choice_data, eligible):
    with app.app_context():
        with pytest.raises(services.ChoiceNotFound):
            remove_choice(choice_data["candidate_ids"][0], 999999)


def test_remove_after_lock_is_rejected(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    with app.app_context():
        choice = add_choice(candidate_id, choice_data["branch_ids"][0])
        from app.choices.models import ChoiceLock
        from app.extensions import db
        db.session.add(ChoiceLock(candidate_id=candidate_id))
        db.session.commit()
        with pytest.raises(services.ChoicesLocked):
            remove_choice(candidate_id, choice.id)
