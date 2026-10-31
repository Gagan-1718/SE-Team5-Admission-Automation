"""Administrator publication API. Browser integration is added separately."""
from flask import Blueprint, flash, g, jsonify, redirect, url_for

from app.accounts.auth import role_required
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
