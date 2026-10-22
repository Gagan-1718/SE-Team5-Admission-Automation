"""all_documents_approved(candidate_id): the check Eligibility depends on."""
import pytest

from app.documents.models import Document
from app.documents.services import REQUIRED_DOCUMENT_TYPES, all_documents_approved
from app.extensions import db

_counter = {"n": 0}


def add(candidate_id, document_type, status):
    _counter["n"] += 1
    db.session.add(Document(candidate_id=candidate_id, application_id=candidate_id,
                            document_type=document_type, stored_name=f"approved-{_counter['n']}.pdf",
                            status=status))
    db.session.commit()


def add_all(candidate_id, status="Approved"):
    for document_type in REQUIRED_DOCUMENT_TYPES:
        add(candidate_id, document_type, status)


def test_required_types_are_the_agreed_three():
    assert set(REQUIRED_DOCUMENT_TYPES) == {"Marksheet", "ID Proof", "Category Certificate"}


def test_no_documents_is_false():
    assert all_documents_approved(1) is False


def test_unknown_or_empty_candidate_is_false():
    add_all(1)
    assert all_documents_approved(999) is False
    assert all_documents_approved(None) is False
    assert all_documents_approved(0) is False


@pytest.mark.parametrize("present", [("Marksheet",), ("Marksheet", "ID Proof"),
                                     ("ID Proof", "Category Certificate")])
def test_missing_required_type_is_false(present):
    for document_type in present:
        add(1, document_type, "Approved")
    assert all_documents_approved(1) is False


def test_only_unrelated_document_types_is_false():
    add(1, "Holiday Photo", "Approved")
    assert all_documents_approved(1) is False


def test_pending_required_document_is_false():
    add(1, "Marksheet", "Approved")
    add(1, "ID Proof", "Approved")
    add(1, "Category Certificate", "Pending")
    assert all_documents_approved(1) is False


def test_rejected_required_document_is_false():
    add(1, "Marksheet", "Rejected")
    add(1, "ID Proof", "Approved")
    add(1, "Category Certificate", "Approved")
    assert all_documents_approved(1) is False


def test_all_required_approved_is_true():
    add_all(1)
    assert all_documents_approved(1) is True


def test_extra_unrelated_document_does_not_matter():
    add_all(1)
    add(1, "Holiday Photo", "Rejected")
    assert all_documents_approved(1) is True


def test_a_second_unapproved_copy_of_a_required_type_blocks_approval():
    add_all(1)
    add(1, "Marksheet", "Pending")
    assert all_documents_approved(1) is False


def test_only_this_candidates_documents_count():
    add_all(1)
    add(2, "Marksheet", "Approved")
    assert all_documents_approved(1) is True
    assert all_documents_approved(2) is False


def test_status_change_is_seen_immediately():
    add_all(1, "Pending")
    assert all_documents_approved(1) is False
    db.session.execute(db.update(Document).where(Document.candidate_id == 1).values(status="Approved"))
    db.session.commit()
    assert all_documents_approved(1) is True
