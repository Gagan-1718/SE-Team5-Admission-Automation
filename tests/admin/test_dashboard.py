"""Administrator dashboard (ADM-F-020): counts match the underlying data."""
import pytest

from app.application.models import Application
from app.documents.models import Document
from app.extensions import db
from tests.catalogue.helpers import login_client


@pytest.fixture
def admin(app):
    return login_client(app, "administrator", 1)


def test_dashboard_page_for_administrator(admin):
    response = admin.get("/admin/dashboard")
    assert response.status_code == 200
    assert b"Administrator dashboard" in response.data


def test_empty_dashboard_json(admin):
    body = admin.get("/admin/dashboard.json").get_json()
    assert body["candidateCounts"] == {"total": 0, "withExamDetails": 0}
    assert body["statusCounts"]["applications"] == {"Draft": 0, "Submitted": 0}
    assert body["statusCounts"]["documents"] == {"Pending": 0, "Approved": 0, "Rejected": 0}
    assert body["pendingDocuments"] == []


def test_counts_match_the_data(app, admin):
    first = login_client(app, "candidate", 2)
    second = login_client(app, "candidate", 3)
    db.session.add(Application(candidate_id=first.user_id, status="Draft"))
    db.session.add(Application(candidate_id=second.user_id, status="Submitted",
                               reference_number="ADM-2026-000002"))
    for number, (status, kind) in enumerate(
            [("Pending", "Marksheet"), ("Pending", "ID Proof"), ("Approved", "Category Certificate"),
             ("Rejected", "Marksheet")], start=1):
        db.session.add(Document(candidate_id=second.user_id, application_id=2, document_type=kind,
                                stored_name=f"file-{number}.pdf", status=status))
    db.session.commit()
    body = admin.get("/admin/dashboard.json").get_json()
    assert body["candidateCounts"]["total"] == 2
    assert body["statusCounts"]["applications"] == {"Draft": 1, "Submitted": 1}
    assert body["statusCounts"]["documents"] == {"Pending": 2, "Approved": 1, "Rejected": 1}
    assert [d["documentType"] for d in body["pendingDocuments"]] == ["Marksheet", "ID Proof"]
    assert b"ID Proof" in admin.get("/admin/dashboard").data


def test_dashboard_access_control(app):
    assert app.test_client().get("/admin/dashboard").status_code == 401
    assert app.test_client().get("/admin/dashboard.json").status_code == 401
    candidate = login_client(app, "candidate", 2)
    assert candidate.get("/admin/dashboard").status_code == 403
    assert candidate.get("/admin/dashboard.json").status_code == 403


def test_dashboard_is_401_after_logout(admin):
    assert admin.get("/admin/dashboard").status_code == 200
    assert admin.post("/accounts/logout").status_code == 204
    assert admin.get("/admin/dashboard").status_code == 401
