"""Administrator dashboard (ADM-F-020).

HTML:  GET /admin/dashboard
JSON:  GET /admin/dashboard.json   {candidateCounts, statusCounts, pendingDocuments}
Anonymous visitors get 401, candidates 403.
"""
from flask import Blueprint, jsonify, render_template

from app.accounts.auth import role_required

from .services import dashboard_summary

bp = Blueprint("admin", __name__)


@bp.get("/admin/dashboard")
@role_required("administrator")
def dashboard_page():
    return render_template("admin/dashboard.html", summary=dashboard_summary())


@bp.get("/admin/dashboard.json")
@role_required("administrator")
def dashboard_json():
    return jsonify(dashboard_summary())
