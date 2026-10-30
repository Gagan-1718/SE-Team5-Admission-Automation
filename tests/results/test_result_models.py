"""Database rules of the result tables (SPRINT_TWO_START_HERE.md section 4.2)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.accounts.models import User
from app.allotment.models import ALLOCATED, AllotmentResult, AllotmentRun
from app.catalogue.models import Branch, Seat
from app.catalogue.seed import seed as seed_catalogue
from app.extensions import db
from app.results.models import ACCEPTED, REJECTED, ResultPublication, SeatDecision


@pytest.fixture
def world(app):
    """A completed run with one allocated result, ready to be published and decided."""
    admin = User(name="Fictional Admin", email="res.admin@example.test", mobile="9300000001",
                 password_hash="not-a-real-hash", role="administrator")
    candidate = User(name="Fictional Candidate", email="res.cand@example.test", mobile="9300000002",
                     password_hash="not-a-real-hash", role="candidate")
    db.session.add_all([admin, candidate])
    seed_catalogue()
    db.session.commit()
    branch = db.session.execute(db.select(Branch).order_by(Branch.id)).scalars().first()
    seat = db.session.execute(db.select(Seat).filter_by(branch_id=branch.id)).scalars().first()
    run = AllotmentRun(run_by=admin.id, candidates_processed=1, allocated_count=1, not_allocated_count=0)
    db.session.add(run)
    db.session.commit()
    allotted = AllotmentResult(run_id=run.id, candidate_id=candidate.id, rank=1, category="General",
                               reference_number="ADM-2026-000001", status=ALLOCATED,
                               branch_id=branch.id, seat_id=seat.id, choice_priority=1)
    db.session.add(allotted)
    db.session.commit()
    return {"admin": admin, "run": run, "result": allotted}


def test_a_run_can_be_published_once(world):
    db.session.add(ResultPublication(run_id=world["run"].id, published_by=world["admin"].id))
    db.session.commit()
    db.session.add(ResultPublication(run_id=world["run"].id, published_by=world["admin"].id))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_a_publication_needs_a_real_run(world):
    db.session.add(ResultPublication(run_id=999999, published_by=world["admin"].id))
    with pytest.raises(IntegrityError):
        db.session.commit()


@pytest.mark.parametrize("decision", [ACCEPTED, REJECTED])
def test_a_result_can_be_decided_once(world, decision):
    db.session.add(SeatDecision(result_id=world["result"].id, decision=decision))
    db.session.commit()
    other = ACCEPTED if decision == REJECTED else REJECTED
    db.session.add(SeatDecision(result_id=world["result"].id, decision=other))
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_a_decision_must_be_accepted_or_rejected(world):
    db.session.add(SeatDecision(result_id=world["result"].id, decision="Undecided"))
    with pytest.raises(IntegrityError):
        db.session.commit()
