"""Document upload routes with an explicit local development fixture."""

import secrets

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.exceptions import RequestEntityTooLarge

from app.documents.services import save_document

bp = Blueprint("documents", __name__, url_prefix="/documents")


def development_identity():
    """Temporary local fixture; replace with real account/application checks."""
    enabled = current_app.config.get("DOCUMENT_DEV_FIXTURE", False)

    if not enabled or not current_app.debug:
        abort(503, description="Document identity integration is not ready.")

    if request.remote_addr not in {"127.0.0.1", "::1"}:
        abort(403)

    return 1, 1


@bp.route("/upload", methods=["GET", "POST"])
def upload():
    candidate_id, application_id = development_identity()

    # Allow multipart overhead beyond the individual file's 2 MiB limit.
    request.max_content_length = 3 * 1024 * 1024

    if "document_upload_token" not in session:
        session["document_upload_token"] = secrets.token_urlsafe(32)

    error = None

    if request.method == "POST":
        supplied_token = request.form.get("csrf_token", "")

        if not secrets.compare_digest(
            supplied_token, session["document_upload_token"]
        ):
            abort(400, description="Invalid form token. Reload the page.")

        try:
            save_document(
                upload=request.files.get("file"),
                candidate_id=candidate_id,
                application_id=application_id,
                document_type=request.form.get("document_type", ""),
            )
        except ValueError as exc:
            error = str(exc)
        else:
            session["document_upload_success"] = True
            return redirect(url_for("documents.upload"))

    success = session.pop("document_upload_success", False)

    return render_template(
        "documents/upload.html",
        csrf_token=session["document_upload_token"],
        error=error,
        success=success,
    ), 400 if error else 200


@bp.errorhandler(RequestEntityTooLarge)
def oversized_request(error):
    return "Upload request too large. Maximum file size is 2 MB.", 413