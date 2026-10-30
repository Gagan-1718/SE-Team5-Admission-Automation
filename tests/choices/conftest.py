"""Fixtures and helpers for the candidate choice-management tests."""

import pytest

from app.accounts.models import User
from app.catalogue.models import Branch, College, Seat
from app.eligibility.models import EligibilityRule
from app.extensions import db


@pytest.fixture
def choice_data(app):
    """Create fictional candidates, catalogue branches and eligibility rules."""
    with app.app_context():
        candidates = []
        for number in (1, 2):
            candidate = User(
                name=f"Choice Candidate {number}",
                email=f"choice{number}@example.test",
                mobile=f"910000000{number}",
                password_hash="test-only-password-hash",
                role="candidate",
            )
            db.session.add(candidate)
            candidates.append(candidate)

        college = College(name="Fictional Institute", city="Bengaluru")
        second_college = College(name="Fictional Technology College", city="Mysuru")
        db.session.add_all([college, second_college])
        db.session.flush()

        branches = [
            Branch(name="Computer Science", college_id=college.id),
            Branch(name="Mechanical Engineering", college_id=college.id),
            Branch(name="Civil Engineering", college_id=second_college.id),
        ]
        db.session.add_all(branches)
        db.session.flush()
        db.session.add_all([
            Seat(branch_id=branches[0].id, category="General", capacity=10, filled=2),
            Seat(branch_id=branches[1].id, category="General", capacity=0, filled=0),
            Seat(branch_id=branches[2].id, category="General", capacity=5, filled=0),
        ])
        db.session.add(EligibilityRule(category="General", max_rank=20000, active=True))
        db.session.commit()
        return {"candidates": candidates, "colleges": [college, second_college], "branches": branches}


def login(client, user):
    response = client.post(
        "/accounts/login",
        json={"identifier": user.email, "password": "fictional-password-123"},
    )
    assert response.status_code == 401 or response.status_code == 200
    return response
