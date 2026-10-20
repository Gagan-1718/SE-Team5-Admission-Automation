"""Private file storage and document metadata persistence."""

from pathlib import Path
from uuid import uuid4

from flask import current_app

from app.extensions import db
from app.documents.models import Document
from app.documents.validation import validate_upload


def save_document(upload, candidate_id, application_id, document_type):
    """Save an upload after the caller verifies identity and application access."""
    if not candidate_id or not application_id:
        raise ValueError("Candidate and application are required.")

    if not isinstance(document_type, str):
        raise ValueError("A valid document type is required.")

    document_type = document_type.strip()

    if not document_type or len(document_type) > 80:
        raise ValueError("A valid document type is required.")

    content, extension = validate_upload(upload)

    configured_directory = current_app.config.get("DOCUMENT_UPLOAD_DIR")
    upload_directory = (
        Path(configured_directory)
        if configured_directory
        else Path(current_app.instance_path) / "uploads"
    )
    upload_directory.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid4().hex}{extension}"
    destination = upload_directory / stored_name

    document = Document(
        candidate_id=candidate_id,
        application_id=application_id,
        document_type=document_type.strip(),
        stored_name=stored_name,
        status="Pending",
    )

    file_created = False

    try:
        with destination.open("xb") as output:
            file_created = True
            output.write(content)

        db.session.add(document)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if file_created:
            destination.unlink(missing_ok=True)
        raise

    return document

class ReviewConflict(ValueError):
    """Raised when a document has already been reviewed."""


def review_document(document_id, decision, reason=None):
    """Review a Pending document after the caller authorizes the admin."""
    if decision not in ("Approved", "Rejected"):
        raise ValueError("Decision must be Approved or Rejected.")

    if reason is not None and not isinstance(reason, str):
        raise ValueError("Rejection reason must be text.")

    reason = (reason or "").strip()

    if decision == "Rejected" and not reason:
        raise ValueError("A rejection reason is required.")

    document = db.session.get(Document, document_id)

    if document is None:
        raise LookupError("Document not found.")

    values = {"status": decision}

    if decision == "Rejected":
        values["rejection_reason"] = reason

    try:
        # Update only Pending records, preventing a second review
        # from overwriting an existing decision.
        result = db.session.execute(
            db.update(Document)
            .where(
                Document.id == document_id,
                Document.status == "Pending",
            )
            .values(**values)
        )

        if result.rowcount != 1:
            raise ReviewConflict("Only Pending documents can be reviewed.")

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return document
class ResubmissionConflict(ValueError):
    """Raised when a document is no longer eligible for replacement."""


def resubmit_document(document_id, candidate_id, upload):
    """Replace an owned Rejected document after the caller authenticates the candidate."""
    from app.documents.storage import save_replacement_file, stored_file_path

    document = db.session.get(Document, document_id)
    if document is None or not candidate_id or document.candidate_id != candidate_id:
        raise LookupError("Document not found.")
    if document.status != "Rejected":
        raise ResubmissionConflict("Only Rejected documents can be resubmitted.")

    original_name = document.stored_name
    original_path = stored_file_path(original_name)
    replacement_name = save_replacement_file(upload)
    try:
        result = db.session.execute(
            db.update(Document)
            .where(
                Document.id == document_id,
                Document.candidate_id == candidate_id,
                Document.status == "Rejected",
                Document.stored_name == original_name,
            )
            .values(stored_name=replacement_name, status="Pending", rejection_reason=None)
        )
        if result.rowcount != 1:
            raise ResubmissionConflict("Document changed; refresh before resubmitting.")
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            stored_file_path(replacement_name).unlink(missing_ok=True)
        except OSError:
            current_app.logger.exception("Could not clean up failed replacement file")
        raise

    # Keep the original until the replacement metadata is durably committed.
    try:
        original_path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.exception("Replacement saved but old document file needs cleanup")
    return document
