"""Audit service. Other modules call record_audit(...) after a privileged action."""
from flask import g

from app.extensions import db

from .models import AuditLog


def record_audit(actor_id, action_type, target_type=None, target_id=None,
                 outcome="Success", actor_role="administrator"):
    """Append one entry and commit it. There is deliberately no update or delete function."""
    entry = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        outcome=outcome,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def record_admin_action(action_type, target_type=None, target_id=None, outcome="Success"):
    """Record an action by the signed-in administrator of the current request."""
    user = getattr(g, "current_user", None)
    if user is None:
        raise RuntimeError("record_admin_action needs a signed-in user")
    return record_audit(user.id, action_type, target_type, target_id, outcome, actor_role=user.role)


def list_audit(action_type=None, limit=200):
    """Newest first. Read-only."""
    stmt = db.select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if action_type:
        stmt = stmt.where(AuditLog.action_type == action_type)
    return db.session.execute(stmt).scalars().all()
