"""Idempotent fictional Accounts seed data."""
import os
import secrets

from sqlalchemy import inspect, text

from app.extensions import db

from .constants import ALLOWED_CATEGORIES, EXAM_TYPES
from .models import ExamRecord, User
from .security import hash_password

EXAM_RECORDS = (
    ("KCET", 1000, "General", 185.0),
    ("KCET", 4500, "OBC", 160.5),
    ("KCET", 12000, "SC", 140.0),
    ("KCET", 15000, "ST", 132.5),
    ("KCET", 9000, "EWS", 150.0),
    ("KCET", 90000, "General", 60.0),
    ("COMEDK", 800, "General", 190.0),
    ("COMEDK", 6000, "OBC", 155.0),
)


def seed():
    """Insert the fictional exam records and administrator exactly once."""
    _ensure_profile_columns()
    for exam_type, rank, category, score in EXAM_RECORDS:
        if exam_type not in EXAM_TYPES or category not in ALLOWED_CATEGORIES:
            raise ValueError("Invalid Accounts seed record.")
        existing = db.session.execute(
            db.select(ExamRecord).where(
                ExamRecord.exam_type == exam_type,
                ExamRecord.rank == rank,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.session.add(
                ExamRecord(
                    exam_type=exam_type,
                    rank=rank,
                    category=category,
                    score=score,
                )
            )

    admin = db.session.execute(
        db.select(User).where(User.email == "admin@example.test")
    ).scalar_one_or_none()
    if admin is None:
        password = os.environ.get("ADMIN_SEED_PASSWORD")
        generated = password is None
        password = password or secrets.token_urlsafe(12)
        db.session.add(
            User(
                name="Fictional Admin",
                email="admin@example.test",
                mobile="9000000000",
                password_hash=hash_password(password),
                role="administrator",
            )
        )
        db.session.commit()
        if generated:
            print(f"Generated ADMIN_SEED_PASSWORD: {password}")
    else:
        db.session.commit()


def _ensure_exam_record_column():
    """Add the new nullable link when using a pre-Day-2 local SQLite file."""
    columns = {column["name"] for column in inspect(db.engine).get_columns("users")}
    if "exam_record_id" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE users ADD COLUMN exam_record_id "
                "INTEGER REFERENCES exam_records(id)"
            )
        )
        db.session.commit()


def _ensure_profile_columns():
    """Idempotently upgrade pre-Sprint-2 users without deleting existing data."""
    columns = {column["name"] for column in inspect(db.engine).get_columns("users")}
    additions = {
        "exam_record_id": "INTEGER REFERENCES exam_records(id)",
        "date_of_birth": "DATE",
        "address_line": "VARCHAR(200)",
        "city": "VARCHAR(100)",
        "pincode": "VARCHAR(6)",
    }
    for name, definition in additions.items():
        if name not in columns:
            db.session.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))
    if set(additions) - columns:
        db.session.commit()
