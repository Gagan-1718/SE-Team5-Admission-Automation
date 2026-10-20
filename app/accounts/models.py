"""Persistent account and server-side session models."""
from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    mobile = db.Column(db.String(20), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="candidate")
    exam_record_id = db.Column(db.Integer, db.ForeignKey("exam_records.id"), nullable=True)
    rank = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(40), nullable=True)
    exam_record = db.relationship("ExamRecord", backref=db.backref("candidates"))

    def identity(self):
        return {
            "id": self.id,
            "role": self.role,
            "rank": self.rank,
            "category": self.category,
        }


class ExamRecord(db.Model):
    __tablename__ = "exam_records"
    __table_args__ = (
        db.UniqueConstraint("exam_type", "rank", name="uq_exam_records_exam_type_rank"),
    )

    id = db.Column(db.Integer, primary_key=True)
    exam_type = db.Column(db.String(20), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Float, nullable=False)


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    token_hash = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    user = db.relationship(User, backref=db.backref("sessions", cascade="all, delete-orphan"))

    def is_expired(self):
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= datetime.now(timezone.utc)

