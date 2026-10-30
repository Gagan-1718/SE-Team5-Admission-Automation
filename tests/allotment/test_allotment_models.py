"""Database rules of the allotment tables (SPRINT_TWO_START_HERE.md section 4.2)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.accounts.models import User
from app.allotment.models import ALLOCATED, NOT_ALLOCATED, AllotmentResult, AllotmentRun
from app.catalogue.models import Branch, Seat
from app.catalogue.seed import seed as seed_catalogue
from app.extensions import db


@pytest.fixture
def world(app):
    """An administrator, a candidate, the seeded catalogue and one completed run."""
    admin = User(name="Fictional Admin", email="allot.admin@example.test", mobile="9200000001",
                 password_hash="not-a-real-hash", role="administrator")
    candidate = User(name="Fictional Candidate", email="allot.cand@example.test", mobile="9200000002",
                     password_hash="not-a-real-hash", role="candidate")
    db.session.add_all([admin, candidate])
    seed_catalogue()
    db.session.commit()
    branch = db.session.execute(db.select(Branch).order_by(Branch.id)).scalars().first()
    seat = db.session.execute(db.select(Seat).filter_by(branch_id=branch.id)).scalars().first()
    run = AllotmentRun(run_by=admin.id, candidates_processed=1, allocated_count=1, not_allocated_count=0)
    db.session.add(run)
    db.session.commit()
    return {"admin": admin, "candidate": candidate, "branch": branch, "seat": seat, "run": run}


def result(world, **overrides):
    values = dict(run_id=world["run"].id, candidate_id=world["candidate"].id, rank=1, category="General",
                  reference_number="ADM-2026-000001", status=ALLOCATED, branch_id=world["branch"].id,
                  seat_id=world["seat"].id, choice_priority=1)
    values.update(overrides)
    return AllotmentResult(**values)


def test_only_one_run_can_exist(world):
    db.session.add(AllotmentRun(run_by=world["admin"].id))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_a_run_cannot_claim_another_cycle(world):
    db.session.rollback()
    db.session.delete(world["run"])
    db.session.commit()
    db.session.add(AllotmentRun(run_by=world["admin"].id, cycle=2))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_run_counts_must_add_up(world):
    db.session.rollback()
    db.session.delete(world["run"])
    db.session.commit()
    db.session.add(AllotmentRun(run_by=world["admin"].id, candidates_processed=5, allocated_count=2,
                                not_allocated_count=2))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_an_allocated_result_with_branch_seat_and_priority_is_accepted(world):
    db.session.add(result(world))
    db.session.commit()
    assert db.session.query(AllotmentResult).count() == 1


def test_a_not_allocated_result_has_no_branch_seat_or_priority(world):
    db.session.add(result(world, status=NOT_ALLOCATED, branch_id=None, seat_id=None, choice_priority=None))
    db.session.commit()
    assert db.session.query(AllotmentResult).one().status == NOT_ALLOCATED


@pytest.mark.parametrize("overrides", [
    {"branch_id": None},                                  # Allocated but no branch
    {"seat_id": None},                                    # Allocated but no seat
    {"choice_priority": None},                            # Allocated but no choice number
    {"status": NOT_ALLOCATED},                            # Not Allocated but still has a branch
    {"status": NOT_ALLOCATED, "seat_id": None, "choice_priority": None},   # ... branch only
    {"status": "Maybe"},                                  # unknown status
])
def test_inconsistent_results_are_refused_by_the_database(world, overrides):
    db.session.add(result(world, **overrides))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_a_candidate_has_one_result_per_run(world):
    db.session.add(result(world))
    db.session.commit()
    db.session.add(result(world, reference_number="ADM-2026-000002"))
    with pytest.raises(IntegrityError):
        db.session.commit()
