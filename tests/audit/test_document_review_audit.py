"""Administrator document reviews are written to the audit log; failed ones are not."""
import pytest

from app.audit.models import AuditLog
from app.application.models import Application
from app.documents.models import Document
from app.extensions import db
from tests.catalogue.helpers import login_client


@pytest.fixture
def document(app):
    candidate = login_client(app, "candidate", 77)
    application = Application(candidate_id=candidate.user_id, status="Submitted",
                              reference_number="ADM-AUDIT-TEST")
    db.session.add(application)
    db.session.commit()
    item = Document(candidate_id=candidate.user_id, application_id=application.id, document_type="Marksheet",
                    stored_name="audit-review.pdf", status="Pending")
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def admin(app):
    client = login_client(app, "administrator", 1)
    assert client.get("/admin/documents").status_code == 200
    with client.session_transaction() as session:
        client.token = session["document_review_token"]
    return client


def decide(admin, document_id, decision, reason=None):
    return admin.post(f"/admin/documents/{document_id}/review",
                      json={"decision": decision, "reason": reason, "csrf_token": admin.token})


def entries():
    db.session.expire_all()
    return db.session.execute(db.select(AuditLog).order_by(AuditLog.id)).scalars().all()


def test_approval_is_audited(admin, document):
    assert decide(admin, document.id, "Approved").status_code == 200
    [entry] = entries()
    assert (entry.action_type, entry.target_type, entry.target_id) == ("document.approve", "document", document.id)
    assert entry.actor_id == admin.user_id and entry.actor_role == "administrator"
    assert entry.outcome == "Success"


def test_rejection_is_audited_without_the_reason(admin, document):
    assert decide(admin, document.id, "Rejected", "Blurry scan of my fictional marksheet").status_code == 200
    [entry] = entries()
    assert entry.action_type == "document.reject" and entry.target_id == document.id
    stored = " ".join(str(v) for v in (entry.action_type, entry.target_type, entry.outcome))
    assert "Blurry" not in stored and "audit-review.pdf" not in stored


@pytest.mark.parametrize("decision, reason, status", [
    ("Rejected", None, 422),       # reason is mandatory
    ("Maybe", None, 422),          # invalid decision
])
def test_invalid_reviews_are_not_audited(admin, document, decision, reason, status):
    assert decide(admin, document.id, decision, reason).status_code == status
    assert entries() == []


def test_unknown_document_is_not_audited(admin):
    assert decide(admin, 9999, "Approved").status_code == 404
    assert entries() == []


def test_second_review_conflict_is_not_audited_again(admin, document):
    assert decide(admin, document.id, "Approved").status_code == 200
    assert decide(admin, document.id, "Rejected", "Changed my mind").status_code == 409
    assert [e.action_type for e in entries()] == ["document.approve"]


def test_bad_token_and_non_admin_are_not_audited(app, admin, document):
    bad = admin.post(f"/admin/documents/{document.id}/review",
                     json={"decision": "Approved", "csrf_token": "wrong"})
    assert bad.status_code == 400
    assert app.test_client().post(f"/admin/documents/{document.id}/review",
                                  json={"decision": "Approved"}).status_code == 401
    candidate = login_client(app, "candidate", 2)
    assert candidate.post(f"/admin/documents/{document.id}/review",
                          json={"decision": "Approved"}).status_code == 403
    assert entries() == []
