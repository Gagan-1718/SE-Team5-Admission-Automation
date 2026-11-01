"""Administrator dashboard and candidate management routes.

HTML:
    GET /admin/dashboard
    GET /admin/candidates

JSON:
    GET /admin/dashboard.json

Anonymous visitors receive 401.
Candidates receive 403.
Only administrators can access these routes.
"""

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import or_

from app.accounts.auth import role_required
from app.accounts.models import User
from app.extensions import db

from .services import dashboard_summary


bp = Blueprint("admin", __name__)


@bp.get("/admin/dashboard")
@role_required("administrator")
def dashboard_page():
    """Display the administrator dashboard."""
    return render_template(
        "admin/dashboard.html",
        summary=dashboard_summary(),
    )


@bp.get("/admin/dashboard.json")
@role_required("administrator")
def dashboard_json():
    """Return administrator dashboard statistics as JSON."""
    return jsonify(dashboard_summary())


@bp.get("/admin/candidates")
@role_required("administrator")
def candidate_list():
    """Display and search registered candidate accounts.

    Supports searching by candidate name, email address or mobile number.
    Only candidate accounts are returned.
    """
    query = request.args.get("q", "").strip()

    stmt = db.select(User).where(User.role == "candidate")

    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                User.name.ilike(pattern),
                User.email.ilike(pattern),
                User.mobile.ilike(pattern),
            )
        )

    candidates = (
        db.session.execute(
            stmt.order_by(User.name, User.id)
        )
        .scalars()
        .all()
    )

    return render_template(
        "admin/candidates.html",
        candidates=candidates,
        query=query,
    )
