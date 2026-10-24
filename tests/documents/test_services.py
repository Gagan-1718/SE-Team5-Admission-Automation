from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from pypdf import PdfWriter
from app.extensions import db
from app.documents.models import Document
from app.documents.services import save_document
from app.documents.validation import UploadValidationError

def pdf_upload(filename="marksheet.pdf"):
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    output.seek(0)

    return FileStorage(
        stream=output,
        filename=filename,
    )

@pytest.fixture
def upload_directory(app, tmp_path):
    directory = tmp_path / "uploads"
    app.config["DOCUMENT_UPLOAD_DIR"] = str(directory)
    return directory


def test_upload_saves_file_and_metadata(app, upload_directory):
    document = save_document(
        pdf_upload(),
        candidate_id=1,
        application_id=1,
        document_type="Marksheet",
    )

    saved = db.session.get(Document, document.id)

    assert saved.candidate_id == 1
    assert saved.application_id == 1
    assert saved.document_type == "Marksheet"
    assert saved.status == "Pending"
    assert saved.stored_name != "marksheet.pdf"
    assert saved.stored_name.endswith(".pdf")
    assert (
    upload_directory / saved.stored_name).read_bytes() == pdf_upload().stream.getvalue()


def test_same_original_filename_does_not_overwrite(app, upload_directory):
    first = save_document(pdf_upload(), 1, 1, "Marksheet")
    second = save_document(pdf_upload(), 1, 1, "Marksheet")

    assert first.stored_name != second.stored_name
    assert len(list(upload_directory.iterdir())) == 2


def test_invalid_upload_creates_no_record_or_file(app, upload_directory):
    invalid = FileStorage(
        stream=BytesIO(b"executable content"),
        filename="invalid.exe",
    )

    with pytest.raises(UploadValidationError):
        save_document(invalid, 1, 1, "Marksheet")

    assert db.session.execute(
        db.select(db.func.count(Document.id))
    ).scalar_one() == 0
    assert not upload_directory.exists()


def test_database_failure_removes_uploaded_file(
    app, upload_directory, monkeypatch
):
    def fail_commit():
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(db.session, "commit", fail_commit)

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        save_document(pdf_upload(), 1, 1, "Marksheet")

    assert list(upload_directory.iterdir()) == []
    assert db.session.execute(
        db.select(db.func.count(Document.id))
    ).scalar_one() == 0


@pytest.mark.parametrize(
    "candidate_id,application_id,document_type",
    [
        (None, 1, "Marksheet"),
        (1, None, "Marksheet"),
        (1, 1, ""),
        (1, 1, " " * 3),
        (1, 1, "x" * 81),
    ],
)
def test_invalid_metadata_is_rejected(
    app, upload_directory, candidate_id, application_id, document_type
):
    with pytest.raises(ValueError):
        save_document(
            pdf_upload(),
            candidate_id,
            application_id,
            document_type,
        )

    assert not upload_directory.exists()

@pytest.mark.parametrize("document_type", ["Marksheet", "ID Proof", "Category Certificate"])
def test_each_allowed_document_type_is_saved(app, upload_directory, document_type):
    document = save_document(pdf_upload(), 1, 1, document_type)
    assert document.document_type == document_type
    assert document.status == "Pending"
    assert (upload_directory / document.stored_name).exists()


@pytest.mark.parametrize("document_type", [
    "Holiday Photo", "marksheet", "ID proof", "", " ", None, 123, [], {},
])
def test_unknown_document_type_creates_no_file_or_metadata(app, upload_directory, document_type):
    with pytest.raises(ValueError, match="Choose Marksheet, ID Proof or Category Certificate"):
        save_document(pdf_upload(), 1, 1, document_type)
    assert not upload_directory.exists()
    assert db.session.execute(db.select(db.func.count(Document.id))).scalar_one() == 0


def test_surrounding_whitespace_is_normalized(app, upload_directory):
    assert save_document(pdf_upload(), 1, 1, "  Marksheet  ").document_type == "Marksheet"


@pytest.mark.parametrize("candidate_id,application_id", [(999, 1), (1, 999)])
def test_invalid_foreign_key_removes_uploaded_file(app, upload_directory, candidate_id, application_id):
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        save_document(pdf_upload(), candidate_id, application_id, "Marksheet")
    assert list(upload_directory.iterdir()) == []
    assert db.session.execute(db.select(db.func.count(Document.id))).scalar_one() == 0
