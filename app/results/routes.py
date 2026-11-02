"""Administrator publication API. Browser integration is added separately."""
from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from app.accounts.auth import role_required, current_candidate_id
from app.application.identity import candidate_page_required
from . import services

bp = Blueprint("results", __name__)


@bp.post("/api/v1/admin/allotment/runs/<int:run_id>/publish")
@role_required("administrator")
def publish_run(run_id):
    # The actor comes exclusively from the authenticated session, never the body.
    try:
        publication = services.publish(run_id, g.current_user.id)
    except services.ResultError as exc:
        return jsonify(error=type(exc).__name__, message=str(exc)), exc.status_code
    return jsonify(
        publication_id=publication.id,
        run_id=publication.run_id,
        published_by=publication.published_by,
        published_at=publication.published_at.isoformat(),
    ), 201


@bp.post("/admin/allotment/runs/<int:run_id>/publish")
@role_required("administrator")
def publish_from_console(run_id):
    """Native form uses the same service as the API and returns to the console."""
    try:
        services.publish(run_id, g.current_user.id)
    except services.ResultError as exc:
        flash(str(exc), "error")
    else:
        flash("Allotment results published successfully.", "success")
    return redirect(url_for("allotment.console"), code=303)


VIEW_MESSAGES = {
    services.NOT_PUBLISHED: "Results will appear here once the administrator publishes them.",
    services.NOT_IN_RUN: "You were not part of this allotment run.",
    services.NOT_ALLOCATED: "None of your locked choices had a seat left in your category.",
    services.ALLOCATED: "Your allotted seat is shown below.",
}


@bp.after_request
def private_results(response):
    response.headers["Cache-Control"] = "private, no-store"
    return response


@bp.get("/result")
@candidate_page_required
def result_page():
    view = services.candidate_view(current_candidate_id())
    return render_template("results/result.html", view=view, message=VIEW_MESSAGES[view["state"]])


@bp.get("/api/v1/allotment/result")
@role_required("candidate")
def result_api():
    view = services.candidate_view(current_candidate_id())
    return jsonify(**view, message=VIEW_MESSAGES[view["state"]]), (
        404 if view["state"] == services.NOT_PUBLISHED else 200
    )


def _save_decision(payload):
    if not isinstance(payload, dict) and not hasattr(payload, "get"):
        raise services.InvalidDecision("A decision is required: Accept or Reject.")
    raw = payload.get("decision")
    if not isinstance(raw, str) or raw not in ("Accept", "Reject"):
        raise services.InvalidDecision("Choose Accept or Reject.")
    return services.decide(current_candidate_id(), "Accepted" if raw == "Accept" else "Rejected")


@bp.post("/api/v1/allotment/decision")
@role_required("candidate")
def decision_api():
    try:
        decision = _save_decision(request.get_json(silent=True))
    except services.ResultError as exc:
        return jsonify(error=type(exc).__name__, message=str(exc)), exc.status_code
    return jsonify(decision=decision.decision, decided_at=decision.decided_at.isoformat()), 201


@bp.post("/result/decision")
@candidate_page_required
def decision_form():
    try:
        _save_decision(request.form)
    except services.ResultError as exc:
        flash(str(exc), "error")
    else:
        flash("Your seat decision has been recorded. It cannot be changed.", "success")
    return redirect(url_for("results.result_page"), code=303)
