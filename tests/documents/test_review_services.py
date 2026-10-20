"""Review decisions must validate input and preserve existing data on failure."""

import pytest

from app.documents.models import Document
from app.documents.services import ReviewConflict, review_document
from app.extensions import db


@pytest.fixture
def pending_document(app):
    document = Document(
        candidate_id=1,
        application_id=1,
        document_type="Marksheet",
        stored_name="fictional-review.pdf",
        status="Pending",
    )
    db.session.add(document)
    db.session.commit()
    return document


def reload_document(document_id):
    db.session.expire_all()
    return db.session.get(Document, document_id)


def test_approve_pending_document(pending_document):
    document_id = pending_document.id
    result = review_document(document_id, "Approved")
    saved = reload_document(document_id)

    assert result.id == document_id
    assert saved.status == "Approved"
    assert saved.rejection_reason is None
    assert saved.candidate_id == 1
    assert saved.application_id == 1
    assert saved.stored_name == "fictional-review.pdf"


def test_reject_persists_trimmed_reason(pending_document):
    document_id = pending_document.id
    review_document(document_id, "Rejected", "  Upload a readable copy.  ")
    saved = reload_document(document_id)

    assert saved.status == "Rejected"
    assert saved.rejection_reason == "Upload a readable copy."


@pytest.mark.parametrize("reason", [None, "", "   ", "\t\n", 123, ["reason"]])
def test_reject_requires_nonempty_text_reason(pending_document, reason):
    document_id = pending_document.id
    with pytest.raises(ValueError):
        review_document(document_id, "Rejected", reason)

    saved = reload_document(document_id)
    assert saved.status == "Pending"
    assert saved.rejection_reason is None


@pytest.mark.parametrize("decision", [None, "Pending", "approved", "invalid", ["Approved"]])
def test_invalid_decision_preserves_pending_document(pending_document, decision):
    document_id = pending_document.id
    with pytest.raises(ValueError, match="Decision must be"):
        review_document(document_id, decision)

    assert reload_document(document_id).status == "Pending"


@pytest.mark.parametrize("initial_status", ["Approved", "Rejected"])
@pytest.mark.parametrize("decision", ["Approved", "Rejected"])
def test_reviewed_document_cannot_be_reviewed_again(pending_document, initial_status, decision):
    document_id = pending_document.id
    pending_document.status = initial_status
    pending_document.rejection_reason = "Original reason" if initial_status == "Rejected" else None
    db.session.commit()

    with pytest.raises(ReviewConflict, match="Only Pending"):
        review_document(document_id, decision, "Replacement reason")

    saved = reload_document(document_id)
    assert saved.status == initial_status
    assert saved.rejection_reason == ("Original reason" if initial_status == "Rejected" else None)


def test_missing_document_raises_lookup_error(app):
    with pytest.raises(LookupError, match="Document not found"):
        review_document(999999, "Approved")


def test_failed_commit_rolls_back_decision_and_reason(pending_document, monkeypatch):
    document_id = pending_document.id

    def fail_commit():
        raise RuntimeError("Simulated review database failure")

    monkeypatch.setattr(db.session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="Simulated review database failure"):
        review_document(document_id, "Rejected", "Unreadable document")

    saved = reload_document(document_id)
    assert saved.status == "Pending"
    assert saved.rejection_reason is None
