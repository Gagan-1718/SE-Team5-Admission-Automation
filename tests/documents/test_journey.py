"""The documents step on the candidate dashboard (journey contract, section 4.4)."""
from app.accounts.models import User
from app.application.models import Application
from app.documents.journey import step_statuses
from app.documents.models import Document
from app.documents.services import REQUIRED_DOCUMENT_TYPES
from app.extensions import db
from app.journey import CURRENT, DONE, LOCKED, PROBLEM, WAITING

_counter = {"n": 0}


def add(candidate_id, document_type, status, reason=None):
    _counter["n"] += 1
    db.session.add(Document(candidate_id=candidate_id, application_id=candidate_id,
                            document_type=document_type, stored_name=f"journey-{_counter['n']}.pdf",
                            status=status, rejection_reason=reason))
    db.session.commit()


def only_step(candidate_id):
    steps = step_statuses(candidate_id)
    assert len(steps) == 1 and steps[0]["key"] == "documents" and steps[0]["href"] == "/documents"
    return steps[0]


def test_locked_until_the_application_is_submitted():
    db.session.add(User(id=4, name="Fictional Draft", email="journey.draft@example.test",
                        mobile="9000000044", password_hash="not-a-real-hash", role="candidate"))
    db.session.add(Application(id=4, candidate_id=4, status="Draft"))
    db.session.commit()
    step = only_step(4)
    assert step["state"] == LOCKED and "Submit your application" in step["detail"]


def test_current_when_nothing_is_uploaded_yet():
    step = only_step(1)
    assert step["state"] == CURRENT and "Upload" in step["detail"]
    for document_type in REQUIRED_DOCUMENT_TYPES:
        assert document_type in step["detail"]


def test_current_names_only_the_missing_types():
    add(1, "Marksheet", "Pending")
    step = only_step(1)
    assert step["state"] == CURRENT
    assert "Marksheet" not in step["detail"] and "ID Proof" in step["detail"]


def test_waiting_when_all_are_uploaded_and_some_are_pending():
    add(1, "Marksheet", "Approved")
    add(1, "ID Proof", "Pending")
    add(1, "Category Certificate", "Pending")
    step = only_step(1)
    assert step["state"] == WAITING and "1 of 3 approved" in step["detail"]


def test_problem_when_a_document_was_rejected_shows_the_reason():
    add(1, "Marksheet", "Rejected", "Fictional reason: blurred scan")
    add(1, "ID Proof", "Approved")
    step = only_step(1)
    assert step["state"] == PROBLEM
    assert "Marksheet" in step["detail"] and "blurred scan" in step["detail"]


def test_done_when_all_three_are_approved():
    for document_type in REQUIRED_DOCUMENT_TYPES:
        add(1, document_type, "Approved")
    step = only_step(1)
    assert step["state"] == DONE and step["detail"] == "All 3 required documents approved."


def test_other_candidates_documents_do_not_count():
    for document_type in REQUIRED_DOCUMENT_TYPES:
        add(2, document_type, "Approved")
    assert only_step(1)["state"] == CURRENT
