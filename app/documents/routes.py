"""Document upload routes with an explicit local development fixture."""

import secrets

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    send_from_directory,
    url_for,
)
from werkzeug.exceptions import RequestEntityTooLarge

from pathlib import Path

from app.extensions import db
from app.documents.models import Document
from app.documents.access import admin_required
from app.documents.services import (
    save_document, review_document, ReviewConflict,
    resubmit_document, ResubmissionConflict,
)

bp = Blueprint("documents", __name__)


def development_identity():
    """Temporary local fixture; replace with real account/application checks."""
    enabled = current_app.config.get("DOCUMENT_DEV_FIXTURE", False)

    if not enabled or not current_app.debug:
        abort(503, description="Document identity integration is not ready.")

    if request.remote_addr not in {"127.0.0.1", "::1"}:
        abort(403)

    return 1, 1


@bp.route("/documents/upload", methods=["GET", "POST"])
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


def review_token():
    if "document_review_token" not in session:
        session["document_review_token"] = secrets.token_urlsafe(32)
    return session["document_review_token"]


def document_json(document):
    return {"id": document.id, "candidate_id": document.candidate_id,
            "document_type": document.document_type, "status": document.status,
            "rejection_reason": document.rejection_reason}


@bp.get("/admin/documents")
@bp.get("/admin/documents.json")
@admin_required
def review_queue():
    status = request.args.get("status", "Pending")
    if status not in ("Pending", "Approved", "Rejected"):
        abort(400, description="Invalid document status.")
    documents = db.session.execute(
        db.select(Document).where(Document.status == status).order_by(Document.id)
    ).scalars().all()
    if request.path.endswith(".json"):
        return jsonify(documents=[document_json(d) for d in documents])
    return render_template("documents/review.html", documents=documents,
                           status=status, csrf_token=review_token())


@bp.post("/admin/documents/<int:document_id>/review")
@admin_required
def review(document_id):
    # Both HTML and JSON writes require the session-bound form token.
    data = request.get_json(silent=True) if request.is_json else request.form
    if not data or not hasattr(data, "get"):
        abort(400)
    supplied = request.headers.get("X-CSRF-Token") or data.get("csrf_token", "")
    expected = session.get("document_review_token")
    if not isinstance(supplied, str) or not expected or not secrets.compare_digest(supplied, expected):
        abort(400, description="Invalid form token. Reload the review queue.")
    try:
        document = review_document(document_id, data.get("decision"), data.get("reason"))
    except LookupError:
        abort(404)
    except ReviewConflict as exc:
        abort(409, description=str(exc))
    except ValueError as exc:
        abort(422, description=str(exc))
    if request.is_json:
        return jsonify(document_json(document))
    return redirect(url_for("documents.review_queue"))


@bp.get("/admin/documents/<int:document_id>/file")
@admin_required
def review_file(document_id):
    document = db.session.get(Document, document_id)
    if document is None:
        abort(404)
    name = document.stored_name
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        abort(404)
    directory = Path(current_app.config.get("DOCUMENT_UPLOAD_DIR")
                     or Path(current_app.instance_path) / "uploads").resolve()
    destination = directory / name
    if destination.resolve().parent != directory or not destination.is_file():
        abort(404)
    response = send_from_directory(directory, name, as_attachment=True)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/documents")
def status_page():
    candidate_id, _ = development_identity()
    documents = db.session.execute(
        db.select(Document)
        .where(Document.candidate_id == candidate_id)
        .order_by(Document.id.desc())
    ).scalars().all()
    response = current_app.make_response(
        render_template("documents/status.html", documents=documents,
                        csrf_token=resubmission_token(),
                        success=session.pop("document_resubmission_success", False))
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def resubmission_token():
    if "document_resubmission_token" not in session:
        session["document_resubmission_token"] = secrets.token_urlsafe(32)
    return session["document_resubmission_token"]


@bp.post("/documents/<int:document_id>/resubmit")
def resubmit(document_id):
    candidate_id, _ = development_identity()
    request.max_content_length = 3 * 1024 * 1024
    supplied = request.form.get("csrf_token", "")
    expected = session.get("document_resubmission_token")
    if not expected or not secrets.compare_digest(supplied, expected):
        abort(400, description="Invalid form token. Reload My documents.")
    try:
        resubmit_document(document_id, candidate_id, request.files.get("file"))
    except LookupError:
        abort(404)
    except ResubmissionConflict as exc:
        abort(409, description=str(exc))
    except ValueError as exc:
        abort(422, description=str(exc))
    session["document_resubmission_success"] = True
    return redirect(url_for("documents.status_page"), code=303)
