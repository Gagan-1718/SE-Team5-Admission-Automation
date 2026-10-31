"""A real-database version of the Test Plan's Appendix B oracle, for the allotment run tests.

Everything is stored exactly as the real modules store it: exam records and users (accounts),
submitted applications (application), approved documents (documents), cut-off rules
(eligibility), colleges and seats (catalogue), choices and locks (choices).
"""
import uuid

import pytest

from app.accounts.models import ExamRecord, User
from app.application.models import SUBMITTED, Application
from app.catalogue.models import Seat
from app.catalogue.services import create_branch, create_college
from app.choices.models import Choice, ChoiceLock
from app.documents.models import Document
from app.documents.services import REQUIRED_DOCUMENT_TYPES
from app.eligibility.seed import seed as seed_rules
from app.extensions import db


class World:
    """Builder for allotment scenarios. Branch names are short keys such as "A-CSE"."""

    def __init__(self):
        self.branches = {}
        self.candidates = {}
        self._mobile = 9600000000
        seed_rules()  # General cut-off 20000, OBC 30000, SC/ST 40000, EWS 25000
        self.admin = self._user("Fictional Admin", "administrator")
        db.session.commit()

    def _user(self, name, role, **extra):
        self._mobile += 1
        user = User(name=name, email=f"{uuid.uuid4().hex[:10]}@example.test", mobile=str(self._mobile),
                    password_hash="not-a-real-hash", role=role, **extra)
        db.session.add(user)
        db.session.flush()
        return user

    def branch(self, key, seats):
        """Create a branch like "A-CSE" (college A) with {category: capacity}."""
        college_key, branch_name = key.split("-", 1)
        college_name = f"Oracle College {college_key}"
        from app.catalogue.services import find_college
        college = find_college(college_name) or create_college(college_name, "Testville")
        branch = create_branch(college, branch_name)
        for category, capacity in seats.items():
            db.session.add(Seat(branch_id=branch.id, category=category, capacity=capacity, filled=0))
        db.session.commit()
        self.branches[key] = branch
        return branch

    def candidate(self, label, rank, choices, category="General", locked=True,
                  documents="Approved", exam_type="KCET"):
        """A candidate with exam details, a submitted application, documents and choices."""
        record = ExamRecord(exam_type=exam_type, rank=rank, category=category, score=100.0)
        db.session.add(record)
        db.session.flush()
        user = self._user(f"Fictional {label}", "candidate", exam_record_id=record.id,
                          rank=rank, category=category)
        application = Application(candidate_id=user.id, status=SUBMITTED, guardian_name="Fictional Guardian",
                                  guardian_mobile="9876543210", school_name="Fictional School",
                                  board="CBSE", percentage=80.0, reference_number="pending")
        db.session.add(application)
        db.session.flush()
        application.reference_number = f"ADM-2026-{application.id:06d}"
        for index, document_type in enumerate(REQUIRED_DOCUMENT_TYPES):
            status = documents if index == 0 else "Approved"
            db.session.add(Document(candidate_id=user.id, application_id=application.id,
                                    document_type=document_type, stored_name=f"{uuid.uuid4().hex}.pdf",
                                    status=status))
        for priority, key in enumerate(choices, start=1):
            db.session.add(Choice(candidate_id=user.id, branch_id=self.branches[key].id, priority=priority))
        if locked:
            db.session.add(ChoiceLock(candidate_id=user.id))
        db.session.commit()
        self.candidates[label] = user
        return user

    def seat(self, key, category="General"):
        db.session.expire_all()
        return db.session.execute(
            db.select(Seat).filter_by(branch_id=self.branches[key].id, category=category)
        ).scalar_one()


@pytest.fixture
def world(app):
    return World()


@pytest.fixture
def oracle(world):
    """Appendix B: seats A-CSE 2, A-ISE 1, B-ECE 1 (General); C1..C5 ranks 1..5, all Eligible."""
    world.branch("A-CSE", {"General": 2})
    world.branch("A-ISE", {"General": 1})
    world.branch("B-ECE", {"General": 1})
    world.candidate("C1", 1, ["A-CSE", "A-ISE"])
    world.candidate("C2", 2, ["A-CSE", "B-ECE"])
    world.candidate("C3", 3, ["A-CSE", "A-ISE"])
    world.candidate("C4", 4, ["A-CSE", "A-ISE"])
    world.candidate("C5", 5, ["A-CSE"])
    return world
