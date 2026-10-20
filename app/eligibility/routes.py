"""Eligibility page and JSON endpoint (owner: Tasya).

HTML:  GET /eligibility
JSON:  GET /api/v1/candidates/me/eligibility
TEMPORARY: both use candidate #1 and need no login until Day 3, when they switch to
accounts' current_candidate_id() with page_login_required / login_required.
"""
from flask import Blueprint, jsonify, render_template

from .services import get_eligibility

bp = Blueprint("eligibility", __name__)

_TEMPORARY_CANDIDATE_ID = 1  # Day 3: replace with current_candidate_id() from accounts


@bp.get("/eligibility")
def eligibility_page():
    result = get_eligibility(_TEMPORARY_CANDIDATE_ID)
    return render_template("eligibility/status.html", result=result)


@bp.get("/api/v1/candidates/me/eligibility")
def eligibility_json():
    return jsonify(get_eligibility(_TEMPORARY_CANDIDATE_ID))
