"""Resubmission preserves ownership and recovers safely from persistence failures."""
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter
from werkzeug.datastructures import FileStorage

from app.documents.models import Document
from app.documents.services import ResubmissionConflict, resubmit_document
from app.extensions import db


def upload():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(stream)
    stream.seek(0)
    return FileStorage(stream=stream, filename="replacement.pdf", content_type="application/pdf")


@pytest.fixture
def rejected(app, tmp_path):
    directory = tmp_path / "uploads"
    directory.mkdir()
    app.config["DOCUMENT_UPLOAD_DIR"] = str(directory)
    (directory / "original.pdf").write_bytes(b"original content")
    document = Document(candidate_id=1, application_id=2, document_type="Marksheet",
                        stored_name="original.pdf", status="Rejected", rejection_reason="Unreadable")
    db.session.add(document)
    db.session.commit()
    return document, directory


def test_replacement_resets_review_and_preserves_identity(rejected):
    document, directory = rejected
    document_id = document.id
    result = resubmit_document(document_id, 1, upload())
    db.session.expire_all()
    assert result.id == document_id
    assert (result.candidate_id, result.application_id, result.document_type) == (1, 2, "Marksheet")
    assert result.status == "Pending"
    assert result.rejection_reason is None
    assert result.stored_name != "original.pdf"
    assert (directory / result.stored_name).read_bytes().startswith(b"%PDF")
    assert not (directory / "original.pdf").exists()


@pytest.mark.parametrize("status", ["Pending", "Approved"])
def test_non_rejected_document_cannot_be_replaced(rejected, status):
    document, directory = rejected
    document.status = status
    db.session.commit()
    with pytest.raises(ResubmissionConflict):
        resubmit_document(document.id, 1, upload())
    assert [p.name for p in directory.iterdir()] == ["original.pdf"]
    assert document.status == status


@pytest.mark.parametrize("candidate_id", [2, None, 0])
def test_other_candidate_cannot_replace_document(rejected, candidate_id):
    document, directory = rejected
    with pytest.raises(LookupError):
        resubmit_document(document.id, candidate_id, upload())
    assert [p.name for p in directory.iterdir()] == ["original.pdf"]
    assert document.status == "Rejected"


def test_missing_document(app):
    with pytest.raises(LookupError):
        resubmit_document(99999, 1, upload())


def test_invalid_upload_preserves_original(rejected):
    document, directory = rejected
    invalid = FileStorage(stream=BytesIO(b"not pdf"), filename="fake.pdf")
    with pytest.raises(ValueError):
        resubmit_document(document.id, 1, invalid)
    assert (directory / "original.pdf").read_bytes() == b"original content"
    assert len(list(directory.iterdir())) == 1
    assert document.rejection_reason == "Unreadable"


def test_commit_failure_preserves_original_and_removes_replacement(rejected, monkeypatch):
    document, directory = rejected
    document_id = document.id
    def fail():
        raise RuntimeError("Database unavailable")
    monkeypatch.setattr(db.session, "commit", fail)
    with pytest.raises(RuntimeError, match="Database unavailable"):
        resubmit_document(document_id, 1, upload())
    saved = db.session.get(Document, document_id)
    assert (saved.status, saved.stored_name, saved.rejection_reason) == ("Rejected", "original.pdf", "Unreadable")
    assert (directory / "original.pdf").read_bytes() == b"original content"
    assert len(list(directory.iterdir())) == 1


def test_old_file_cleanup_failure_does_not_undo_success(rejected, monkeypatch, caplog):
    document, directory = rejected
    original_unlink = Path.unlink
    def fail_old(path, *args, **kwargs):
        if path.name == "original.pdf":
            raise PermissionError("File locked")
        return original_unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", fail_old)
    result = resubmit_document(document.id, 1, upload())
    assert result.status == "Pending"
    assert (directory / result.stored_name).exists()
    assert "old document file needs cleanup" in caplog.text
