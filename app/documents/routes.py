"""Documents linked to authenticated accounts and submitted applications."""

import secrets

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
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

from app.audit.services import record_admin_action
from app.extensions import db
from app.security import csrf_protection_enabled, csrf_token as central_csrf_token
from app.documents.models import Document
from app.documents.access import admin_required
from app.documents.services import (
    REQUIRED_DOCUMENT_TYPES, save_document, review_document, ReviewConflict,
    resubmit_document, ResubmissionConflict,
)

from app.accounts.auth import current_candidate_id
from app.accounts.models import User
from app.application.models import Application
from app.application.identity import candidate_page_required
from app.application.services import get_submitted_application

bp = Blueprint("documents", __name__)


@bp.after_request
def private_document_response(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


def submitted_identity():
    """Resolve only the signed-in candidate's submitted application."""
    candidate_id = current_candidate_id()
    application = get_submitted_application(candidate_id)
    if application is None:
        abort(409, description="Submit your application before uploading documents.")
    return candidate_id, application.id


@bp.route("/documents/upload", methods=["GET", "POST"])
@candidate_page_required
def upload():
    candidate_id, application_id = submitted_identity()

    # Allow multipart overhead beyond the individual file's 2 MiB limit.
    request.max_content_length = 3 * 1024 * 1024

    document_form_token("document_upload_token")

    error = None

    if request.method == "POST":
        supplied_token = request.form.get("csrf_token", "")

        if not csrf_protection_enabled() and not secrets.compare_digest(
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
        document_types=REQUIRED_DOCUMENT_TYPES,
        csrf_token=session["document_upload_token"],
        error=error,
        success=success,
    ), 400 if error else 200


@bp.errorhandler(RequestEntityTooLarge)
def oversized_request(error):
    return "Upload request too large. Maximum file size is 2 MB.", 413


def document_form_token(key):
    if csrf_protection_enabled():
        session[key] = central_csrf_token()
    elif key not in session:
        session[key] = secrets.token_urlsafe(32)
    return session[key]


def review_token():
    return document_form_token("document_review_token")


def document_json(document):
    return {"id": document.id, "candidate_id": document.candidate_id,
            "document_type": document.document_type, "status": document.status,
            "rejection_reason": document.rejection_reason}


@bp.get("/admin/documents")
@bp.get("/admin/documents.json", endpoint="review_queue_json")
@admin_required
def review_queue():
    status = request.args.get("status", "Pending")
    if status not in ("Pending", "Approved", "Rejected"):
        abort(400, description="Invalid document status.")
    documents = db.session.execute(
        db.select(Document).where(Document.status == status).order_by(Document.id.desc())
    ).scalars().all()
    if request.path.endswith(".json"):
        return jsonify(documents=[document_json(d) for d in documents])
    counts = dict(db.session.execute(
        db.select(Document.status, db.func.count()).group_by(Document.status)).all())
    candidates = list(dict.fromkeys(d.candidate_id for d in documents))
    pages = max(1, -(-len(candidates) // CANDIDATES_PER_PAGE))
    page = min(max(request.args.get("page", 1, type=int), 1), pages)
    shown = candidates[(page - 1) * CANDIDATES_PER_PAGE:page * CANDIDATES_PER_PAGE]
    return render_template("documents/review.html", groups=candidate_groups(shown),
                           candidate_total=len(candidates), page=page, pages=pages,
                           counts=counts, status=status, csrf_token=review_token())


CANDIDATES_PER_PAGE = 20


def candidate_groups(order):
    """One entry per candidate id in ``order``, with all of that candidate's documents.

    The queue is filtered by status, but the reviewer sees the candidate's full set so a
    marksheet can be checked against the ID proof and category certificate beside it.
    """
    if not order:
        return []
    people = {cid: (name, reference) for cid, name, reference in db.session.execute(
        db.select(User.id, User.name, Application.reference_number)
        .outerjoin(Application, Application.candidate_id == User.id)
        .where(User.id.in_(order))
    )}
    owned = {cid: [] for cid in order}
    for document in db.session.execute(
        db.select(Document).where(Document.candidate_id.in_(order)).order_by(Document.id.desc())
    ).scalars():
        owned[document.candidate_id].append(document)
    rank = {name: index for index, name in enumerate(REQUIRED_DOCUMENT_TYPES)}
    groups = []
    for cid in order:
        name, reference = people.get(cid, (f"Candidate {cid}", None))
        docs = sorted(owned[cid], key=lambda d: rank.get(d.document_type, len(rank)))
        uploaded = {d.document_type for d in docs}
        groups.append({
            "name": name,
            "reference": reference,
            "documents": docs,
            "missing": [t for t in REQUIRED_DOCUMENT_TYPES if t not in uploaded],
            "required": len(REQUIRED_DOCUMENT_TYPES),
            "approved": sum(d.status == "Approved" for d in docs),
            "pending": sum(d.status == "Pending" for d in docs),
        })
    return groups


@bp.post("/admin/documents/<int:document_id>/review")
@admin_required
def review(document_id):
    # Both HTML and JSON writes require the session-bound form token.
    data = request.get_json(silent=True) if request.is_json else request.form
    if not data or not hasattr(data, "get"):
        abort(400)
    supplied = request.headers.get("X-CSRF-Token") or data.get("csrf_token", "")
    expected = session.get("document_review_token")
    if not csrf_protection_enabled() and (
        not isinstance(supplied, str) or not expected or not secrets.compare_digest(supplied, expected)
    ):
        abort(400, description="Invalid form token. Reload the review queue.")
    decision = data.get("decision")
    try:
        document = review_document(document_id, decision, data.get("reason"))
    except LookupError:
        abort(404)
    except (ReviewConflict, ValueError) as exc:
        if not request.is_json:  # the browser form shows the problem on the queue page
            flash(str(exc), "error")
            return redirect(url_for("documents.review_queue"))
        abort(409 if isinstance(exc, ReviewConflict) else 422, description=str(exc))
    # Only reached when the review succeeded. The entry holds ids and the decision, never
    # the rejection reason or any file name.
    record_admin_action(
        "document.approve" if decision == "Approved" else "document.reject",
        "document",
        document.id,
    )
    if request.is_json:
        return jsonify(document_json(document))
    flash(f"{document.document_type} {'approved' if decision == 'Approved' else 'rejected'}.", "success")
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
@candidate_page_required
def status_page():
    candidate_id = current_candidate_id()
    documents = db.session.execute(
        db.select(Document)
        .where(Document.candidate_id == candidate_id)
        .order_by(Document.id.desc())
    ).scalars().all()
    response = current_app.make_response(
        render_template("documents/status.html", documents=documents,
                        required_types=REQUIRED_DOCUMENT_TYPES,
                        csrf_token=resubmission_token(),
                        success=session.pop("document_resubmission_success", False))
    )
    response.headers["Cache-Control"] = "no-store"
    return response


def resubmission_token():
    return document_form_token("document_resubmission_token")


@bp.post("/documents/<int:document_id>/resubmit")
@candidate_page_required
def resubmit(document_id):
    candidate_id, application_id = submitted_identity()
    document = db.session.get(Document, document_id)
    if document is None or document.candidate_id != candidate_id or document.application_id != application_id:
        abort(404)
    request.max_content_length = 3 * 1024 * 1024
    supplied = request.form.get("csrf_token", "")
    expected = session.get("document_resubmission_token")
    if not csrf_protection_enabled() and (
        not expected or not secrets.compare_digest(supplied, expected)
    ):
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
