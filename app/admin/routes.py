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
from app.application.models import Application
from app.extensions import db

from .services import cycle_overview, dashboard_summary


bp = Blueprint("admin", __name__)
PER_PAGE = 25


@bp.get("/admin/dashboard")
@role_required("administrator")
def dashboard_page():
    """Display the administrator dashboard."""
    return render_template(
        "admin/dashboard.html",
        summary=dashboard_summary(),
        overview=cycle_overview(),
    )


@bp.get("/admin/dashboard.json")
@role_required("administrator")
def dashboard_json():
    """Return administrator dashboard statistics as JSON."""
    return jsonify(dashboard_summary())


@bp.get("/admin/candidates")
@role_required("administrator")
def candidate_list():
    """Search registered candidates by name, email or mobile, 25 per page, with application status."""
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    filters = [User.role == "candidate"]
    if query:
        pattern = f"%{query}%"
        filters.append(or_(User.name.ilike(pattern), User.email.ilike(pattern), User.mobile.ilike(pattern)))

    total = db.session.scalar(db.select(db.func.count(User.id)).where(*filters))
    pages = max(1, -(-total // PER_PAGE))
    page = min(max(page, 1), pages)
    rows = db.session.execute(
        db.select(User, Application.status, Application.reference_number)
        .outerjoin(Application, Application.candidate_id == User.id)
        .where(*filters)
        .order_by(User.name, User.id)
        .limit(PER_PAGE).offset((page - 1) * PER_PAGE)
    ).all()

    return render_template("admin/candidates.html", rows=rows, query=query,
                           total=total, page=page, pages=pages)
