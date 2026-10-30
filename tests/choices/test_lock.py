import pytest

from app.choices import services
from app.choices.models import ChoiceLock
from app.choices.services import add_choice, lock
from app.extensions import db


@pytest.fixture
def eligible(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "fictional test eligibility"
    })


def test_non_empty_list_locks_with_timestamp(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    with app.app_context():
        add_choice(candidate_id, choice_data["branch_ids"][0])
        row = lock(candidate_id)
        assert row.candidate_id == candidate_id
        assert row.locked_at is not None
        assert services.is_locked(candidate_id)


def test_empty_list_cannot_be_locked(app, choice_data):
    with app.app_context():
        with pytest.raises(services.NothingToLock, match="Add at least one choice first"):
            lock(choice_data["candidate_ids"][0])


def test_locking_twice_is_rejected(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    with app.app_context():
        add_choice(candidate_id, choice_data["branch_ids"][0])
        lock(candidate_id)
        with pytest.raises(services.ChoicesLocked):
            lock(candidate_id)
        assert db.session.query(ChoiceLock).count() == 1


def test_every_mutation_is_rejected_after_lock(app, choice_data, eligible):
    candidate_id = choice_data["candidate_ids"][0]
    branch_ids = choice_data["branch_ids"]
    with app.app_context():
        choice = add_choice(candidate_id, branch_ids[0])
        lock(candidate_id)
        with pytest.raises(services.ChoicesLocked):
            add_choice(candidate_id, branch_ids[1])
        with pytest.raises(services.ChoicesLocked):
            services.remove_choice(candidate_id, choice.id)
        with pytest.raises(services.ChoicesLocked):
            services.reorder(candidate_id, [choice.id])
