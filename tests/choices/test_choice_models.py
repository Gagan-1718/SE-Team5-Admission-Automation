"""Database rules of the choices tables (SPRINT_TWO_START_HERE.md section 4.2)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.accounts.models import User
from app.catalogue.seed import seed as seed_catalogue
from app.catalogue.models import Branch
from app.choices.models import Choice, ChoiceLock
from app.extensions import db


@pytest.fixture
def candidate(app):
    user = User(name="Fictional Candidate", email="choice.model@example.test", mobile="9100000001",
                password_hash="not-a-real-hash", role="candidate")
    db.session.add(user)
    seed_catalogue()
    db.session.commit()
    return user


def two_branches():
    return db.session.execute(db.select(Branch).order_by(Branch.id).limit(2)).scalars().all()


def test_a_candidate_can_hold_several_different_branches(candidate):
    first, second = two_branches()
    db.session.add_all([Choice(candidate_id=candidate.id, branch_id=first.id, priority=1),
                        Choice(candidate_id=candidate.id, branch_id=second.id, priority=2)])
    db.session.commit()
    assert db.session.query(Choice).count() == 2


def test_the_same_branch_twice_is_refused_by_the_database(candidate):
    first, _ = two_branches()
    db.session.add(Choice(candidate_id=candidate.id, branch_id=first.id, priority=1))
    db.session.commit()
    db.session.add(Choice(candidate_id=candidate.id, branch_id=first.id, priority=2))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_priority_must_be_one_or_more(candidate):
    first, _ = two_branches()
    db.session.add(Choice(candidate_id=candidate.id, branch_id=first.id, priority=0))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_a_choice_needs_a_real_branch_and_a_real_candidate(candidate):
    db.session.add(Choice(candidate_id=candidate.id, branch_id=999999, priority=1))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
    first, _ = two_branches()
    db.session.add(Choice(candidate_id=999999, branch_id=first.id, priority=1))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_a_candidate_has_at_most_one_lock(candidate):
    db.session.add(ChoiceLock(candidate_id=candidate.id))
    db.session.commit()
    assert db.session.get(ChoiceLock, candidate.id).locked_at is not None
    db.session.add(ChoiceLock(candidate_id=candidate.id))
    with pytest.raises(IntegrityError):
        db.session.commit()
