"""Private replacement storage; database decisions stay in the service layer."""

from pathlib import Path
from uuid import uuid4

from flask import current_app

from app.documents.validation import validate_upload


def upload_directory():
    configured = current_app.config.get("DOCUMENT_UPLOAD_DIR")
    return Path(configured or Path(current_app.instance_path) / "uploads").resolve()


def stored_file_path(stored_name):
    """Reject traversal and symlinks escaping the configured private directory."""
    if (not isinstance(stored_name, str) or not stored_name
            or "/" in stored_name or "\\" in stored_name
            or ":" in stored_name or stored_name in (".", "..")):
        raise ValueError("Invalid stored filename.")
    directory = upload_directory()
    path = directory / stored_name
    if path.resolve().parent != directory:
        raise ValueError("Stored file must remain in private upload storage.")
    return path


def save_replacement_file(upload):
    """Validate first, write a unique file, and clean up a partial failed write."""
    content, extension = validate_upload(upload)
    directory = upload_directory()
    directory.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    path = stored_file_path(stored_name)
    created = False
    try:
        with path.open("xb") as output:
            created = True
            output.write(content)
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise
    return stored_name
