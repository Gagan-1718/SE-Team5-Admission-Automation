import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.documents.models import Document


def test_document_is_saved_with_pending_status(app):
    document = Document(
        candidate_id=1,
        application_id=1,
        document_type="marksheet",
        stored_name="fictional-marksheet.pdf",
    )

    db.session.add(document)
    db.session.commit()
    document_id = document.id
    db.session.expire_all()

    saved = db.session.get(Document, document_id)

    assert saved.candidate_id == 1
    assert saved.application_id == 1
    assert saved.document_type == "marksheet"
    assert saved.stored_name == "fictional-marksheet.pdf"
    assert saved.status == "Pending"
    assert saved.rejection_reason is None


def test_invalid_document_status_is_rejected(app):
    document = Document(
        candidate_id=1,
        application_id=1,
        document_type="marksheet",
        stored_name="fictional-invalid-status.pdf",
        status="Unknown",
    )

    db.session.add(document)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()