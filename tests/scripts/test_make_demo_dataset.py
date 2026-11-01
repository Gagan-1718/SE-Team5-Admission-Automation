"""Tests for the deterministic demo dataset generator."""

import os

import pytest
from pypdf import PdfReader

from scripts import make_demo_dataset as generator
from app.extensions import db
from app.accounts.models import User, ExamRecord
from app.application.models import Application
from app.documents.models import Document

from app.catalogue.seed import seed as seed_catalogue
from app.eligibility.seed import seed as seed_eligibility
from app.choices.models import Choice, ChoiceLock
from app.catalogue.models import Branch, Seat
from app.eligibility.services import get_eligibility
from app.catalogue.seed import seed as seed_catalogue
from app.eligibility.seed import seed as seed_eligibility
@pytest.fixture
def demo_environment(app, tmp_path, monkeypatch):
    """Prepare an isolated database and upload directory for demo tests."""

    from app.catalogue.seed import seed as seed_catalogue
    from app.eligibility.seed import seed as seed_eligibility

    upload_dir = tmp_path / "demo-uploads"

    monkeypatch.setattr(
        generator,
        "upload_directory",
        lambda: upload_dir,
    )

    monkeypatch.setenv(
        "DEMO_CANDIDATE_PASSWORD",
        "test-demo-password",
    )

    with app.app_context():
        # Seed the catalogue branches and seat matrix.
        seed_catalogue()

        # Seed the eligibility rules.
        seed_eligibility()

        yield upload_dir

def run_generator(candidate_count=10, seed=1):
    """Run the generator inside the active Flask application context."""
    generator.generate_dataset(candidate_count, seed)


def get_demo_users():
    return db.session.execute(
        db.select(User).where(
            User.email.like("cand%@example.test")
        ).order_by(User.email)
    ).scalars().all()


def test_generator_creates_candidates_applications_and_documents(
    app,
    demo_environment,
):
    with app.app_context():
        seed_catalogue()
        seed_eligibility()
        run_generator(candidate_count=10, seed=1)

        users = get_demo_users()

        assert len(users) == 10

        for user in users:
            application = db.session.execute(
                db.select(Application).where(
                    Application.candidate_id == user.id
                )
            ).scalar_one_or_none()

            assert application is not None
            assert application.status == "Submitted"
            assert application.reference_number

            documents = db.session.execute(
                db.select(Document).where(
                    Document.candidate_id == user.id
                )
            ).scalars().all()

            assert len(documents) == 3


def test_generator_creates_valid_pdf_documents(
    app,
    demo_environment,
):
    with app.app_context():
        run_generator(candidate_count=10, seed=1)

        pdf_files = list(demo_environment.glob("*.pdf"))

        assert len(pdf_files) == 30

        for pdf_file in pdf_files:
            reader = PdfReader(str(pdf_file))

            assert len(reader.pages) == 1


def test_document_status_distribution(
    app,
    demo_environment,
):
    with app.app_context():
        run_generator(candidate_count=10, seed=1)

        users = get_demo_users()

        pending_or_rejected_candidates = 0

        for user in users:
            documents = db.session.execute(
                db.select(Document).where(
                    Document.candidate_id == user.id
                )
            ).scalars().all()

            statuses = [document.status for document in documents]

            if any(
                status in ("Pending", "Rejected")
                for status in statuses
            ):
                pending_or_rejected_candidates += 1

        # Exactly one of the ten candidates belongs to group 8.
        assert pending_or_rejected_candidates == 1


def test_generator_is_idempotent_and_reproducible(
    app,
    demo_environment,
):
    with app.app_context():
        run_generator(candidate_count=20, seed=7)

        def snapshot():
            users = get_demo_users()
            result = []

            for user in users:
                application = db.session.execute(
                    db.select(Application).where(
                        Application.candidate_id == user.id
                    )
                ).scalar_one()

                documents = db.session.execute(
                    db.select(Document).where(
                        Document.candidate_id == user.id
                    ).order_by(Document.document_type)
                ).scalars().all()

                result.append({
                    "email": user.email,
                    "name": user.name,
                    "rank": user.rank,
                    "category": user.category,
                    "application_status": application.status,
                    "reference_number": application.reference_number,
                    "percentage": application.percentage,
                    "documents": [
                        (
                            document.document_type,
                            document.status,
                            document.rejection_reason,
                        )
                        for document in documents
                    ],
                })

            return result

        before = snapshot()

        run_generator(candidate_count=20, seed=7)

        after = snapshot()

        assert before == after

        # Rerunning must not create duplicate records.
        assert db.session.query(User).filter(
            User.email.like("cand%@example.test")
        ).count() == 20

        assert db.session.query(Application).count() == 20

        assert db.session.query(Document).count() == 60


@pytest.mark.parametrize(
    "candidate_count",
    [0, -10, 5, 11],
)
def test_generator_rejects_invalid_candidate_counts(
    app,
    demo_environment,
    candidate_count,
):
    with app.app_context():
        with pytest.raises(ValueError):
            run_generator(candidate_count=candidate_count, seed=1)


def test_generator_requires_demo_password(
    app,
    demo_environment,
    monkeypatch,
):
    monkeypatch.delenv("DEMO_CANDIDATE_PASSWORD", raising=False)

    with app.app_context():
        with pytest.raises(ValueError, match="DEMO_CANDIDATE_PASSWORD"):
            run_generator(candidate_count=10, seed=1)


def test_generator_does_not_change_existing_password(
    app,
    demo_environment,
):
    with app.app_context():
        run_generator(candidate_count=10, seed=1)

        user = db.session.execute(
            db.select(User).where(
                User.email == "cand0001@example.test"
            )
        ).scalar_one()

        original_password_hash = user.password_hash

        user.password_hash = "existing-password-hash"
        db.session.commit()

        run_generator(candidate_count=10, seed=1)

        db.session.refresh(user)

        assert user.password_hash == "existing-password-hash"
        assert user.password_hash != original_password_hash


def test_generator_rejects_existing_non_candidate_account(
    app,
    demo_environment,
):
    with app.app_context():
        run_generator(candidate_count=10, seed=1)

        user = db.session.execute(
            db.select(User).where(
                User.email == "cand0001@example.test"
            )
        ).scalar_one()

        user.role = "admin"
        db.session.commit()

        with pytest.raises(ValueError, match="not a candidate"):
            run_generator(candidate_count=10, seed=1)


def test_generator_uses_same_seed_for_same_exam_values(
    app,
    demo_environment,
):
    with app.app_context():
        run_generator(candidate_count=10, seed=42)

        first_run = [
            (
                record.exam_type,
                record.rank,
                record.category,
                record.score,
            )
            for record in db.session.execute(
                db.select(ExamRecord).order_by(ExamRecord.rank)
            ).scalars().all()
        ]

        run_generator(candidate_count=10, seed=42)

        second_run = [
            (
                record.exam_type,
                record.rank,
                record.category,
                record.score,
            )
            for record in db.session.execute(
                db.select(ExamRecord).order_by(ExamRecord.rank)
            ).scalars().all()
        ]

        assert first_run == second_run


def test_generator_creates_expected_number_of_exam_records(
    app,
    demo_environment,
):
    with app.app_context():
        run_generator(candidate_count=30, seed=1)

        demo_records = db.session.execute(
            db.select(ExamRecord).where(
                ExamRecord.exam_type == "KCET"
            )
        ).scalars().all()

        assert len(demo_records) == 30
def test_generator_creates_choices_and_locks(app, demo_environment):
    with app.app_context():
        run_generator(candidate_count=100, seed=1)

        users = get_demo_users()

        for index, user in enumerate(users):
            group = index % 10

            choices = db.session.scalars(
                db.select(Choice)
                .where(Choice.candidate_id == user.id)
                .order_by(Choice.priority)
            ).all()

            lock = db.session.get(ChoiceLock, user.id)

            if group in range(7) or group == 9:
                assert 3 <= len(choices) <= 6
                assert [c.priority for c in choices] == list(
                    range(1, len(choices) + 1)
                )
                assert len({c.branch_id for c in choices}) == len(choices)
                assert (lock is not None) == (group != 9)
            else:
                assert choices == []
                assert lock is None


def test_generator_preserves_choices_and_locks_on_rerun(
    app, demo_environment
):
    with app.app_context():
        run_generator(candidate_count=30, seed=1)

        before = [
            (
                choice.candidate_id,
                choice.branch_id,
                choice.priority,
            )
            for choice in db.session.scalars(
                db.select(Choice).order_by(
                    Choice.candidate_id, Choice.priority
                )
            ).all()
        ]

        locked_before = sorted(
            db.session.scalars(db.select(ChoiceLock.candidate_id)).all()
        )

        run_generator(candidate_count=30, seed=1)

        after = [
            (
                choice.candidate_id,
                choice.branch_id,
                choice.priority,
            )
            for choice in db.session.scalars(
                db.select(Choice).order_by(
                    Choice.candidate_id, Choice.priority
                )
            ).all()
        ]

        locked_after = sorted(
            db.session.scalars(db.select(ChoiceLock.candidate_id)).all()
        )

        assert before == after
        assert locked_before == locked_after


def test_generator_does_not_change_seat_matrix(app, demo_environment):
    with app.app_context():
        before = [
            (seat.branch_id, seat.category, seat.capacity, seat.filled)
            for seat in db.session.scalars(
                db.select(Seat).order_by(Seat.branch_id, Seat.category)
            ).all()
        ]

        run_generator(candidate_count=30, seed=1)

        after = [
            (seat.branch_id, seat.category, seat.capacity, seat.filled)
            for seat in db.session.scalars(
                db.select(Seat).order_by(Seat.branch_id, Seat.category)
            ).all()
        ]

        assert before == after
        assert sum(row[2] for row in after) == 240
