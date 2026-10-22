"""Eligibility page and JSON endpoint (owner: Tasya).

HTML:  GET /eligibility                      anonymous -> redirect to login, administrator -> 403
JSON:  GET /api/v1/candidates/me/eligibility anonymous -> 401, administrator -> 403,
       no exam details entered -> 422 "exam details not entered" (SAD 4.3.5)
The page shows Pending when exam details are missing.
Both use the signed-in candidate's real exam details and document approval status.
"""
from flask import Blueprint, abort, jsonify, render_template

from app.accounts.auth import current_candidate_id, page_login_required, role_required

from .services import ExamDetailsNotEntered, get_eligibility

bp = Blueprint("eligibility", __name__)


@bp.get("/eligibility")
@page_login_required
def eligibility_page():
    candidate_id = current_candidate_id()
    if candidate_id is None:
        abort(403)
    return render_template("eligibility/status.html", result=get_eligibility(candidate_id))


@bp.get("/api/v1/candidates/me/eligibility")
@role_required("candidate")
def eligibility_json():
    try:
        return jsonify(get_eligibility(current_candidate_id(), require_exam_details=True))
    except ExamDetailsNotEntered:
        return jsonify(error="exam_details_not_entered", message="exam details not entered"), 422
