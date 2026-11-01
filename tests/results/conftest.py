"""Shared fictional allocation for result/decision service and HTTP tests."""
import pytest

from app.accounts.models import ExamRecord, User
from app.accounts.security import hash_password
from app.allotment.models import AllotmentRun, AllotmentResult
from app.catalogue.models import Branch, Seat
from app.catalogue.seed import seed
from app.choices.models import Choice, ChoiceLock
from app.extensions import db

PASSWORD = "fictional-result-password"


@pytest.fixture(scope="session")
def result_password_hash():
    return hash_password(PASSWORD)


@pytest.fixture
def result_world(app, result_password_hash):
    users = {}
    for number, key in enumerate(("admin", "allocated", "not_allocated", "outsider"), 1):
        user = User(name=f"Fictional {key}", email=f"{key}@results.example.test",
                    mobile=f"940000000{number}", password_hash=result_password_hash,
                    role="administrator" if key == "admin" else "candidate")
        db.session.add(user)
        users[key] = user
    db.session.commit()
    exam = ExamRecord(exam_type="KCET", rank=1000, category="General", score=185)
    db.session.add(exam)
    db.session.flush()
    users["allocated"].exam_record_id = exam.id
    users["allocated"].rank, users["allocated"].category = 1000, "General"
    seed()
    db.session.commit()
    branches = db.session.execute(db.select(Branch).order_by(Branch.id)).scalars().all()
    seat = db.session.execute(db.select(Seat).filter_by(
        branch_id=branches[0].id, category="General")).scalar_one()
    seat.filled = 1
    for priority, branch in enumerate(branches[:2], 1):
        db.session.add(Choice(candidate_id=users["allocated"].id, branch_id=branch.id, priority=priority))
    db.session.add(ChoiceLock(candidate_id=users["allocated"].id))
    run = AllotmentRun(run_by=users["admin"].id, candidates_processed=2,
                       allocated_count=1, not_allocated_count=1)
    db.session.add(run)
    db.session.commit()
    allocated = AllotmentResult(
        run_id=run.id, candidate_id=users["allocated"].id, rank=1000, category="General",
        reference_number="ADM-2026-000001", status="Allocated", branch_id=branches[0].id,
        seat_id=seat.id, choice_priority=1)
    unallocated = AllotmentResult(
        run_id=run.id, candidate_id=users["not_allocated"].id, rank=1001, category="General",
        reference_number="ADM-2026-000002", status="Not Allocated")
    db.session.add_all([allocated, unallocated])
    db.session.commit()

    def client_for(key="allocated"):
        client = app.test_client()
        response = client.post("/accounts/login", json={
            "identifier": users[key].email, "password": PASSWORD})
        assert response.status_code == 200, response.json
        return client

    return {"users": users, "run": run, "allocated": allocated, "not_allocated": unallocated,
            "seat": seat, "branch": branches[0], "client": client_for}
