"""Read-only audit log for administrators (SEC-F-005).

HTML:  GET /admin/audit-logs
JSON:  GET /admin/audit-logs.json     [{actor, timestamp, actionType, target}]
Optional filter: ?action_type=college.create. There is no POST, PUT or DELETE route.
"""
from flask import Blueprint, jsonify, render_template, request

from app.accounts.auth import role_required
from app.accounts.models import User
from app.extensions import db

from .services import list_audit

bp = Blueprint("audit", __name__)


@bp.get("/admin/audit-logs")
@role_required("administrator")
def audit_page():
    action_type = request.args.get("action_type", "").strip() or None
    entries = list_audit(action_type)
    actor_ids = {e.actor_id for e in entries if e.actor_id}
    names = dict(db.session.execute(
        db.select(User.id, User.name).where(User.id.in_(actor_ids))).all()) if actor_ids else {}
    return render_template(
        "audit/log.html", entries=entries, names=names, action_type=action_type or ""
    )


@bp.get("/admin/audit-logs.json")
@role_required("administrator")
def audit_json():
    action_type = request.args.get("action_type", "").strip() or None
    return jsonify([entry.as_dict() for entry in list_audit(action_type)])
