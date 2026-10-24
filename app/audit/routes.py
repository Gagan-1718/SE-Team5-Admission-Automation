"""Read-only audit log for administrators (SEC-F-005).

HTML:  GET /admin/audit-logs
JSON:  GET /admin/audit-logs.json     [{actor, timestamp, actionType, target}]
Optional filter: ?action_type=college.create. There is no POST, PUT or DELETE route.
"""
from flask import Blueprint, jsonify, render_template, request

from app.accounts.auth import role_required

from .services import list_audit

bp = Blueprint("audit", __name__)


@bp.get("/admin/audit-logs")
@role_required("administrator")
def audit_page():
    action_type = request.args.get("action_type", "").strip() or None
    return render_template(
        "audit/log.html", entries=list_audit(action_type), action_type=action_type or ""
    )


@bp.get("/admin/audit-logs.json")
@role_required("administrator")
def audit_json():
    action_type = request.args.get("action_type", "").strip() or None
    return jsonify([entry.as_dict() for entry in list_audit(action_type)])
