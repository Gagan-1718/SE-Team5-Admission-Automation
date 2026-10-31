"""Application draft pages and JSON API (owner: Gagan).

HTML:  GET/POST /application, POST /application/submit
JSON:  POST /api/v1/applications, PUT /api/v1/applications/<id>, GET /api/v1/applications/me,
       POST /api/v1/applications/<id>/submit
Errors use the team's body {status, error, message} (SAD A-20).
All routes need a logged-in candidate: pages redirect to the login page, the API returns 401/403.
"""
from http import HTTPStatus

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app.accounts.services import get_exam_details
from app.extensions import db

from . import services
from .identity import candidate_page_required, candidate_required, current_candidate_id
from .models import FORM_FIELDS, Application

bp = Blueprint("application", __name__)


def _error(code, message, **extra):
    body = {"status": code, "error": HTTPStatus(code).phrase, "message": message}
    body.update(extra)
    return jsonify(body), code


def _application_json(application):
    return {
        "applicationId": application.id,
        "candidateId": application.candidate_id,
        "status": application.status,
        "referenceNumber": application.reference_number,
        "fields": application.fields(),
    }


def _owned_application(application_id):
    """Return (application, None) or (None, error response). Candidates see only their own."""
    application = db.session.get(Application, application_id)
    if application is None:
        return None, _error(404, "Application not found.")
    if application.candidate_id != current_candidate_id():
        return None, _error(403, "You can only access your own application.")
    return application, None


# ---------------------------------------------------------------- HTML form

def _render_form(application, values, errors, code=200):
    page = render_template(
        "application/draft.html",
        application=application,
        values=values,
        errors=errors,
        boards=services.BOARDS,
        has_exam_details=get_exam_details(current_candidate_id()) is not None,
    )
    return page, code


@bp.get("/application")
@candidate_page_required
def draft_form():
    application = services.get_for_candidate(current_candidate_id())
    values = application.fields() if application else {}
    return _render_form(application, values, {})


@bp.post("/application")
@candidate_page_required
def save_draft_form():
    candidate_id = current_candidate_id()
    posted = {name: request.form[name] for name in FORM_FIELDS if name in request.form}
    try:
        services.save_draft(candidate_id, posted)
    except services.ValidationError as exc:
        application = services.get_for_candidate(candidate_id)
        return _render_form(application, posted, exc.errors, 422)
    except services.ApplicationLocked:
        application = services.get_for_candidate(candidate_id)
        flash("This application is already submitted and cannot be edited.")
        return _render_form(application, application.fields(), {}, 409)
    flash("Draft saved. You can come back and continue editing later.")
    return redirect(url_for("application.draft_form"))


@bp.post("/application/submit")
@candidate_page_required
def submit_form():
    """Save what is typed, then submit. Missing fields keep the application a Draft."""
    candidate_id = current_candidate_id()
    posted = {name: request.form[name] for name in FORM_FIELDS if name in request.form}
    try:
        application = services.get_for_candidate(candidate_id)
        if application is None:
            application = services.create_draft(candidate_id, posted)
        else:
            services.update_draft(application, posted)
        services.submit(application)
    except services.ValidationError as exc:
        application = services.get_for_candidate(candidate_id)
        return _render_form(application, posted, exc.errors, 422)
    except services.ApplicationLocked:
        application = services.get_for_candidate(candidate_id)
        flash("This application is already submitted.")
        return _render_form(application, application.fields(), {}, 409)
    flash(f"Application submitted. Your reference number is {application.reference_number}.")
    return redirect(url_for("application.draft_form"))


# ---------------------------------------------------------------- JSON API

@bp.post("/api/v1/applications")
@candidate_required
def api_create_draft():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error(400, "Send a JSON object with the application fields.")
    try:
        application = services.create_draft(current_candidate_id(), data)
    except services.ValidationError as exc:
        return _error(422, "Some fields are invalid.", fields=exc.errors)
    except services.ApplicationExists:
        return _error(409, "This candidate already has an application.")
    return jsonify(applicationId=application.id, status=application.status), 201


@bp.put("/api/v1/applications/<int:application_id>")
@candidate_required
def api_save_draft(application_id):
    application, failure = _owned_application(application_id)
    if failure:
        return failure
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error(400, "Send a JSON object with the application fields.")
    try:
        services.update_draft(application, data)
    except services.ValidationError as exc:
        return _error(422, "Some fields are invalid.", fields=exc.errors)
    except services.ApplicationLocked:
        return _error(409, "The application is already submitted.")
    return jsonify(_application_json(application))


@bp.post("/api/v1/applications/<int:application_id>/submit")
@candidate_required
def api_submit(application_id):
    application, failure = _owned_application(application_id)
    if failure:
        return failure
    try:
        services.submit(application)
    except services.ValidationError as exc:
        return _error(422, "Mandatory fields are missing.", fields=exc.errors)
    except services.ApplicationLocked:
        return _error(409, "The application is already submitted.")
    return jsonify(referenceNumber=application.reference_number, status=application.status)


@bp.get("/api/v1/applications/me")
@candidate_required
def api_my_application():
    application = services.get_for_candidate(current_candidate_id())
    if application is None:
        return _error(404, "No application started yet.")
    return jsonify(_application_json(application))
