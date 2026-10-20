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