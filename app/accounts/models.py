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
    rank = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(40), nullable=True)

    def identity(self):
        return {
            "id": self.id,
            "role": self.role,
            "rank": self.rank,
            "category": self.category,
        }


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

