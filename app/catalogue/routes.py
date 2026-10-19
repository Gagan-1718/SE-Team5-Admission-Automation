"""Catalogue pages.

Candidate:  GET /colleges                       list + filter colleges and branches
Admin:      GET  /admin/colleges                all colleges, branches and seat totals
            GET/POST /admin/colleges/new        add a college
            GET/POST /admin/colleges/<id>/edit  edit a college
            GET/POST /admin/colleges/<id>/branches/new   add a branch
            GET/POST /admin/branches/<id>/edit  rename a branch
            GET/POST /admin/branches/<id>/seats category-wise seat capacity

Discovered automatically by app/__init__.py (blueprint named ``bp``).
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db

from .access import admin_required
from .models import SEAT_CATEGORIES, Branch, CatalogueError, College, DuplicateError
from .services import (
    create_branch,
    create_college,
    list_catalogue,
    set_branch_seats,
    update_branch,
    update_college,
)

bp = Blueprint("catalogue", __name__)

DUPLICATE_STATUS = 409
INVALID_STATUS = 422


def _error_status(exc):
    return DUPLICATE_STATUS if isinstance(exc, DuplicateError) else INVALID_STATUS


# ---------------------------------------------------------------- candidate
@bp.get("/colleges")
def candidate_list():
    query = request.args.get("q", "").strip()
    college_id = request.args.get("college_id", type=int)
    all_colleges = db.session.execute(
        db.select(College).order_by(db.func.lower(College.name))
    ).scalars().all()
    results = list_catalogue(query=query, college_id=college_id)
    return render_template(
        "catalogue/candidate_list.html",
        results=results,
        all_colleges=all_colleges,
        query=query,
        college_id=college_id,
        categories=SEAT_CATEGORIES,
    )


# -------------------------------------------------------------------- admin
@bp.get("/admin/colleges")
@admin_required
def admin_index():
    colleges = db.session.execute(
        db.select(College).order_by(db.func.lower(College.name))
    ).scalars().all()
    return render_template("catalogue/admin_index.html", colleges=colleges)


@bp.route("/admin/colleges/new", methods=["GET", "POST"])
@admin_required
def college_new():
    form = {"name": "", "city": ""}
    if request.method == "POST":
        form = {"name": request.form.get("name", ""), "city": request.form.get("city", "")}
        try:
            college = create_college(form["name"], form["city"])
        except CatalogueError as exc:
            return render_template(
                "catalogue/college_form.html", college=None, form=form, error=str(exc)
            ), _error_status(exc)
        flash(f"College '{college.name}' added.")
        return redirect(url_for("catalogue.admin_index"))
    return render_template("catalogue/college_form.html", college=None, form=form, error=None)


@bp.route("/admin/colleges/<int:college_id>/edit", methods=["GET", "POST"])
@admin_required
def college_edit(college_id):
    college = db.get_or_404(College, college_id)
    form = {"name": college.name, "city": college.city}
    if request.method == "POST":
        form = {"name": request.form.get("name", ""), "city": request.form.get("city", "")}
        try:
            update_college(college, form["name"], form["city"])
        except CatalogueError as exc:
            db.session.rollback()
            return render_template(
                "catalogue/college_form.html", college=college, form=form, error=str(exc)
            ), _error_status(exc)
        flash(f"College '{college.name}' updated.")
        return redirect(url_for("catalogue.admin_index"))
    return render_template("catalogue/college_form.html", college=college, form=form, error=None)


@bp.route("/admin/colleges/<int:college_id>/branches/new", methods=["GET", "POST"])
@admin_required
def branch_new(college_id):
    college = db.get_or_404(College, college_id)
    form = {"name": ""}
    if request.method == "POST":
        form = {"name": request.form.get("name", "")}
        try:
            branch = create_branch(college, form["name"])
        except CatalogueError as exc:
            return render_template(
                "catalogue/branch_form.html", college=college, branch=None, form=form, error=str(exc)
            ), _error_status(exc)
        flash(f"Branch '{branch.name}' added to {college.name}. Now set its seat capacity.")
        return redirect(url_for("catalogue.seats_edit", branch_id=branch.id))
    return render_template(
        "catalogue/branch_form.html", college=college, branch=None, form=form, error=None
    )


@bp.route("/admin/branches/<int:branch_id>/edit", methods=["GET", "POST"])
@admin_required
def branch_edit(branch_id):
    branch = db.get_or_404(Branch, branch_id)
    form = {"name": branch.name}
    if request.method == "POST":
        form = {"name": request.form.get("name", "")}
        try:
            update_branch(branch, form["name"])
        except CatalogueError as exc:
            db.session.rollback()
            return render_template(
                "catalogue/branch_form.html",
                college=branch.college,
                branch=branch,
                form=form,
                error=str(exc),
            ), _error_status(exc)
        flash(f"Branch '{branch.name}' updated.")
        return redirect(url_for("catalogue.admin_index"))
    return render_template(
        "catalogue/branch_form.html", college=branch.college, branch=branch, form=form, error=None
    )


@bp.route("/admin/branches/<int:branch_id>/seats", methods=["GET", "POST"])
@admin_required
def seats_edit(branch_id):
    branch = db.get_or_404(Branch, branch_id)

    def current_values():
        return {
            category: (str(branch.seat_for(category).capacity) if branch.seat_for(category) else "")
            for category in SEAT_CATEGORIES
        }

    values = current_values()
    if request.method == "POST":
        values = {category: request.form.get(category, "") for category in SEAT_CATEGORIES}
        try:
            set_branch_seats(branch, values)
        except CatalogueError as exc:
            db.session.rollback()
            return render_template(
                "catalogue/seats_form.html",
                branch=branch,
                categories=SEAT_CATEGORIES,
                values=values,
                error=str(exc),
            ), _error_status(exc)
        flash(f"Seat capacity saved for {branch.name}.")
        return redirect(url_for("catalogue.admin_index"))
    return render_template(
        "catalogue/seats_form.html",
        branch=branch,
        categories=SEAT_CATEGORIES,
        values=values,
        error=None,
    )
