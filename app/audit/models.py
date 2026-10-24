"""Append-only audit log table (SEC-F-005, SAD A-17).

The application has no update or delete path for these rows, and SQLite triggers
reject UPDATE and DELETE even if someone tries them directly. INSERT and SELECT work.
"""
from datetime import datetime, timezone

from sqlalchemy import DDL, event

from app.extensions import db


def _now():
    return datetime.now(timezone.utc)


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    # Plain integer, no foreign key: the log must outlive any record it refers to.
    actor_id = db.Column(db.Integer, nullable=False, index=True)
    actor_role = db.Column(db.String(30), nullable=False, default="administrator")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_now)
    action_type = db.Column(db.String(60), nullable=False, index=True)
    target_type = db.Column(db.String(40), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    outcome = db.Column(db.String(20), nullable=False, default="Success")

    def as_dict(self):
        created = self.created_at
        if created is not None and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return {
            "id": self.id,
            "actor": self.actor_id,
            "actorRole": self.actor_role,
            "timestamp": created.isoformat() if created else None,
            "actionType": self.action_type,
            "target": {"type": self.target_type, "id": self.target_id},
            "outcome": self.outcome,
        }


_NO_UPDATE = DDL(
    "CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log "
    "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END"
)
_NO_DELETE = DDL(
    "CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log "
    "BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END"
)
event.listen(AuditLog.__table__, "after_create", _NO_UPDATE.execute_if(dialect="sqlite"))
event.listen(AuditLog.__table__, "after_create", _NO_DELETE.execute_if(dialect="sqlite"))
