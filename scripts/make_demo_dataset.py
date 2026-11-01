"""Generate deterministic fictional candidate data for demonstrations.

Usage:
    DEMO_CANDIDATE_PASSWORD='fictional-pass-1' \
        python scripts/make_demo_dataset.py --candidates 300 --seed 1

The database must already be initialized and seeded.
This script does not create, reset, or seed database tables.
"""

import argparse
import os
import random
import sys

from io import BytesIO
from pathlib import Path

# Make the project root importable when this file is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pypdf import PdfWriter

from app import create_app
from app.extensions import db

from app.accounts.models import User, ExamRecord
from app.accounts.security import hash_password
from app.accounts.constants import ALLOWED_CATEGORIES

from app.application.models import Application, SUBMITTED
from app.application.services import make_reference_number

from app.documents.models import Document
from app.documents.storage import upload_directory

from app.choices.models import Choice, ChoiceLock
from app.catalogue.models import Branch
from app.eligibility.services import get_eligibility
from app.eligibility.evaluation import (
    ELIGIBLE,
    PENDING,
    NOT_ELIGIBLE,
)


DOCUMENT_TYPES = (
    ("Marksheet", "marksheet"),
    ("ID Proof", "id-proof"),
    ("Category Certificate", "category-certificate"),
)

BOARDS = (
    "Karnataka State PUC",
    "CBSE",
    "ICSE",
    "Other",
)

FIRST_NAMES = (
    "Aarav", "Ananya", "Ishaan", "Diya", "Kabir",
    "Meera", "Rohan", "Saanvi", "Aditya", "Nisha",
)

LAST_NAMES = (
    "Sharma", "Rao", "Patel", "Nair", "Reddy",
    "Kumar", "Das", "Iyer", "Menon", "Joshi",
)

ELIGIBLE_RANK_START = 100
NOT_ELIGIBLE_RANK_START = 50000

DEMO_EMAIL_PREFIX = "cand"
DEMO_EMAIL_DOMAIN = "@example.test"


def make_placeholder_pdf(title):
    """Create a small valid, one-page PDF for demo document downloads."""
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)

    writer.add_metadata({
        "/Title": f"Demo placeholder - {title}",
        "/Subject": "Fictional admission demo document",
    })

    output = BytesIO()
    writer.write(output)

    return output.getvalue()


def candidate_email(number):
    return f"{DEMO_EMAIL_PREFIX}{number:04d}{DEMO_EMAIL_DOMAIN}"


def candidate_mobile(number):
    return str(9700000000 + number)


def candidate_name(number, rng):
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)

    return f"{first} {last} Candidate {number:04d}"


def candidate_group(index):
    """Return the deterministic 10% distribution bucket."""
    return index % 10


def make_exam_values(index, group, rng):
    """Return a unique exam record for this generated candidate."""

    if group == 7:
        rank = NOT_ELIGIBLE_RANK_START + index + 1
    else:
        rank = ELIGIBLE_RANK_START + index + 1

    category = rng.choice(ALLOWED_CATEGORIES)
    score = round(rng.uniform(70.0, 199.0), 2)

    return {
        "exam_type": "KCET",
        "rank": rank,
        "category": category,
        "score": score,
    }


def get_or_create_exam_record(values):
    """Reuse an identical exam record or create a new one."""

    record = db.session.execute(
        db.select(ExamRecord).where(
            ExamRecord.exam_type == values["exam_type"],
            ExamRecord.rank == values["rank"],
        )
    ).scalar_one_or_none()

    if record is not None:
        if (
            record.category != values["category"]
            or record.score != values["score"]
        ):
            raise ValueError(
                f"Exam record conflict for {values['exam_type']} "
                f"rank {values['rank']}. Use the same seed as the "
                "original generation."
            )

        return record, False

    record = ExamRecord(**values)

    db.session.add(record)
    db.session.flush()

    return record, True


def document_statuses(group, rng):
    """Return the three document statuses for a candidate.

    Group 8 receives one Pending or Rejected document.
    All other groups receive three Approved documents.
    """

    statuses = ["Approved", "Approved", "Approved"]
    reasons = [None, None, None]

    if group == 8:
        if rng.choice((True, False)):
            statuses[0] = "Pending"
        else:
            statuses[0] = "Rejected"
            reasons[0] = (
                "Demo rejection: document needs clearer details."
            )

    return statuses, reasons


def ensure_document_files(candidate_number, directory, pdf_contents):
    """Create three valid document files if they do not already exist."""

    directory.mkdir(parents=True, exist_ok=True)

    stored_names = []

    for document_type, slug in DOCUMENT_TYPES:
        stored_name = (
            f"demo-candidate-{candidate_number:04d}-{slug}.pdf"
        )

        path = directory / stored_name

        if not path.exists():
            with path.open("xb") as output:
                output.write(pdf_contents[slug])

        stored_names.append(stored_name)

    return stored_names


def ensure_candidate_choices(user, group, seed, index):
    """Create deterministic choices and permanent locks.

    Groups 0-6:
        Eligible candidates with 3-6 choices and permanent locks.

    Group 7:
        Not Eligible candidates with no choices or locks.

    Group 8:
        Pending candidates with no choices or locks.

    Group 9:
        Eligible candidates with 3-6 choices but no lock.

    Existing choices are never replaced or deleted. Existing locked
    choices must match the deterministic expected choices.
    """

    eligibility = get_eligibility(user.id)
    actual_status = eligibility["status"]

    expected_status = {
        7: NOT_ELIGIBLE,
        8: PENDING,
    }.get(group, ELIGIBLE)

    if actual_status != expected_status:
        raise ValueError(
            f"Eligibility mismatch for {user.email}: "
            f"expected {expected_status}, got {actual_status}. "
            "Check the seeded eligibility rules and candidate documents."
        )

    existing_choices = db.session.execute(
        db.select(Choice)
        .where(Choice.candidate_id == user.id)
        .order_by(Choice.priority)
    ).scalars().all()

    existing_lock = db.session.get(ChoiceLock, user.id)

    # Not Eligible and Pending candidates must not have choices or locks.
    if group in (7, 8):
        if existing_choices or existing_lock is not None:
            raise ValueError(
                f"{user.email} is in group {group}, but already has "
                "choices or a permanent lock. The generator will not "
                "delete or modify them."
            )

        return 0, 0

    branches = db.session.execute(
        db.select(Branch).order_by(Branch.id)
    ).scalars().all()

    if len(branches) < 6:
        raise ValueError(
            "At least six seeded catalogue branches are required "
            "to generate demo choices."
        )

    # Use an independent RNG so choice generation does not change
    # candidate names, exam values, application percentages or documents.
    choice_rng = random.Random(f"choices:{seed}:{index}")

    choice_count = choice_rng.randint(3, 6)
    selected_branches = choice_rng.sample(branches, choice_count)
    expected_branch_ids = [
        branch.id for branch in selected_branches
    ]

    actual_branch_ids = [
        choice.branch_id for choice in existing_choices
    ]

    actual_priorities = [
        choice.priority for choice in existing_choices
    ]

    if existing_choices:
        if actual_branch_ids != expected_branch_ids:
            raise ValueError(
                f"Existing choices for {user.email} do not match "
                "the deterministic choices for this seed. "
                "Existing choices will not be replaced."
            )

        expected_priorities = list(range(1, len(existing_choices) + 1))

        if actual_priorities != expected_priorities:
            raise ValueError(
                f"Existing choice priorities for {user.email} "
                "are not consecutive starting at 1."
            )

    else:
        for priority, branch in enumerate(selected_branches, start=1):
            db.session.add(
                Choice(
                    candidate_id=user.id,
                    branch_id=branch.id,
                    priority=priority,
                )
            )

    created_lock = 0

    # Groups 0-6 are permanently locked.
    if group != 9:
        if existing_lock is None:
            db.session.add(ChoiceLock(candidate_id=user.id))
            created_lock = 1

    # Group 9 is eligible but intentionally remains unlocked.
    elif existing_lock is not None:
        raise ValueError(
            f"{user.email} belongs to the unlocked group but already "
            "has a permanent choice lock. The generator will not "
            "remove it."
        )

    created_choices = 0 if existing_choices else choice_count

    return created_choices, created_lock


def generate_dataset(candidate_count, seed):
    """Create or update the requested number of fictional candidates."""

    if candidate_count <= 0 or candidate_count % 10 != 0:
        raise ValueError(
            "Candidate count must be a positive multiple of 10."
        )

    password = os.environ.get("DEMO_CANDIDATE_PASSWORD", "")

    if not password.strip():
        raise ValueError(
            "Set DEMO_CANDIDATE_PASSWORD before running the generator."
        )

    # Hash once and reuse for every newly created demo account.
    shared_password_hash = hash_password(password)

    directory = upload_directory()

    pdf_contents = {
        slug: make_placeholder_pdf(document_type)
        for document_type, slug in DOCUMENT_TYPES
    }

    created_users = 0
    created_exam_records = 0
    created_applications = 0
    created_documents = 0
    created_choices = 0
    created_locks = 0

    try:
        for index in range(candidate_count):
            number = index + 1
            group = candidate_group(index)
            email = candidate_email(number)

            # Each candidate has an independent RNG.
            candidate_rng = random.Random(f"{seed}:{index}")

            # Generate the name on every run to preserve the RNG sequence.
            generated_name = candidate_name(number, candidate_rng)

            exam_values = make_exam_values(
                index,
                group,
                candidate_rng,
            )

            exam, exam_was_created = get_or_create_exam_record(
                exam_values
            )

            if exam_was_created:
                created_exam_records += 1

            user = db.session.execute(
                db.select(User).where(User.email == email)
            ).scalar_one_or_none()

            if user is None:
                mobile = candidate_mobile(number)

                mobile_owner = db.session.execute(
                    db.select(User).where(User.mobile == mobile)
                ).scalar_one_or_none()

                if mobile_owner is not None:
                    raise ValueError(
                        f"Mobile number {mobile} is already used by "
                        f"another account. Cannot create {email}."
                    )

                user = User(
                    name=generated_name,
                    email=email,
                    mobile=mobile,
                    password_hash=shared_password_hash,
                    role="candidate",
                    exam_record_id=exam.id,
                    rank=exam.rank,
                    category=exam.category,
                )

                db.session.add(user)
                db.session.flush()

                created_users += 1

            else:
                if user.role != "candidate":
                    raise ValueError(
                        f"{email} already exists but is not a candidate."
                    )

                # Keep existing account passwords unchanged.
                user.exam_record_id = exam.id
                user.rank = exam.rank
                user.category = exam.category

            application = db.session.execute(
                db.select(Application).where(
                    Application.candidate_id == user.id
                )
            ).scalar_one_or_none()

            if application is None:
                application = Application(candidate_id=user.id)

                db.session.add(application)
                db.session.flush()

                created_applications += 1

            application.status = SUBMITTED

            application.reference_number = (
                application.reference_number
                or make_reference_number(application.id)
            )

            application.guardian_name = (
                f"Demo Guardian {number:04d}"
            )

            application.guardian_mobile = str(
                9800000000 + number
            )

            application.school_name = (
                f"Demo School {number:04d}"
            )

            application.board = BOARDS[index % len(BOARDS)]

            application.percentage = round(
                candidate_rng.uniform(65.0, 99.0),
                2,
            )

            stored_names = ensure_document_files(
                number,
                directory,
                pdf_contents,
            )

            statuses, reasons = document_statuses(
                group,
                candidate_rng,
            )

            for doc_index, (document_type, slug) in enumerate(
                DOCUMENT_TYPES
            ):
                stored_name = stored_names[doc_index]

                existing = db.session.execute(
                    db.select(Document).where(
                        Document.candidate_id == user.id,
                        Document.document_type == document_type,
                    )
                ).scalar_one_or_none()

                if existing is None:
                    document = Document(
                        candidate_id=user.id,
                        application_id=application.id,
                        document_type=document_type,
                        stored_name=stored_name,
                        status=statuses[doc_index],
                        rejection_reason=reasons[doc_index],
                    )

                    db.session.add(document)
                    created_documents += 1

                else:
                    existing.application_id = application.id
                    existing.stored_name = stored_name
                    existing.status = statuses[doc_index]
                    existing.rejection_reason = reasons[doc_index]

            # Flush document changes before checking eligibility.
            db.session.flush()

            new_choices, new_locks = ensure_candidate_choices(
                user=user,
                group=group,
                seed=seed,
                index=index,
            )

            created_choices += new_choices
            created_locks += new_locks

        # All database changes are committed together.
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    print("\nDemo dataset generation complete.")
    print(f"Requested candidates: {candidate_count}")
    print(f"New candidate accounts: {created_users}")
    print(f"New exam records: {created_exam_records}")
    print(f"New applications: {created_applications}")
    print(f"New document records: {created_documents}")
    print(f"New choices: {created_choices}")
    print(f"New permanent locks: {created_locks}")
    print(f"Document directory: {directory}")

    print("\nExpected eligibility distribution:")
    print(f"  Eligible:     {candidate_count * 8 // 10}")
    print(f"  Not Eligible: {candidate_count // 10}")
    print(f"  Pending:      {candidate_count // 10}")

    print("\nExpected choice distribution:")
    print(f"  Locked:       {candidate_count * 7 // 10}")
    print(f"  Unlocked:     {candidate_count // 10}")
    print(f"  No choices:   {candidate_count * 2 // 10}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate fictional admission demo candidates."
    )

    parser.add_argument(
        "--candidates",
        type=int,
        default=300,
        help="Number of candidates to generate (positive multiple of 10).",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Seed used to generate reproducible candidate data.",
    )

    args = parser.parse_args()

    if args.candidates <= 0 or args.candidates % 10 != 0:
        parser.error(
            "--candidates must be a positive multiple of 10."
        )

    app = create_app()

    try:
        with app.app_context():
            generate_dataset(args.candidates, args.seed)

    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
