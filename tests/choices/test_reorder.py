import pytest

from app.choices import services
from app.choices.services import add_choice, reorder


@pytest.fixture
def eligible(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "fictional test eligibility"
    })


def _three_choices(app, choice_data):
    candidate_id = choice_data["candidate_ids"][0]
    with app.app_context():
        rows = [add_choice(candidate_id, branch_id) for branch_id in choice_data["branch_ids"]]
        return candidate_id, [row.id for row in rows]


def test_reorder_persists_contiguous_priorities(app, choice_data, eligible):
    candidate_id, ids = _three_choices(app, choice_data)
    with app.app_context():
        rows = reorder(candidate_id, [ids[2], ids[0], ids[1]])
        assert [row.id for row in rows] == [ids[2], ids[0], ids[1]]
        assert [row.priority for row in rows] == [1, 2, 3]

        persisted = services.list_choices(candidate_id)
        assert [row.id for row in persisted] == [ids[2], ids[0], ids[1]]


@pytest.mark.parametrize("bad_order", [[], [1], [1, 1, 2], [1, 2, 999999], "not-a-list"])
def test_invalid_reorder_does_not_change_the_saved_order(app, choice_data, eligible, bad_order):
    candidate_id, ids = _three_choices(app, choice_data)
    with app.app_context():
        before = [row.id for row in services.list_choices(candidate_id)]
        with pytest.raises(services.OrderMismatch):
            reorder(candidate_id, bad_order)
        assert [row.id for row in services.list_choices(candidate_id)] == before


def test_locked_reorder_is_rejected(app, choice_data, eligible):
    candidate_id, ids = _three_choices(app, choice_data)
    with app.app_context():
        from app.choices.models import ChoiceLock
        from app.extensions import db
        db.session.add(ChoiceLock(candidate_id=candidate_id))
        db.session.commit()
        with pytest.raises(services.ChoicesLocked):
            reorder(candidate_id, list(reversed(ids)))
