"""get_eligibility, the candidate page and the JSON endpoint, using real exam details and login."""
import pathlib
import re

import pytest

from app.accounts.models import ExamRecord, User
from app.application.models import Application
from app.documents.models import Document
from app.eligibility import services
from app.eligibility.seed import seed
from app.extensions import db
from tests.catalogue.helpers import login_client


@pytest.fixture(autouse=True)
def seeded_rules(app):
    seed()


def _give_exam_details(user_id, rank, category):
    record = ExamRecord(exam_type="KCET", rank=rank, category=category, score=100.0)
    db.session.add(record)
    db.session.flush()
    user = db.session.get(User, user_id)
    user.exam_record_id = record.id
    user.rank, user.category = rank, category
    db.session.commit()


def _documents(monkeypatch, approved):
    monkeypatch.setattr(services, "all_documents_approved", lambda candidate_id: approved)


def _upload(candidate_id, status, kinds=("Marksheet", "ID Proof", "Category Certificate")):
    application = Application(candidate_id=candidate_id, status="Submitted",
                              reference_number=f"ADM-ELIGIBILITY-{candidate_id}")
    db.session.add(application)
    db.session.commit()
    for kind in kinds:
        db.session.add(Document(candidate_id=candidate_id, application_id=application.id, document_type=kind,
                                stored_name=f"{candidate_id}-{kind}-{status}.pdf", status=status))
    db.session.commit()


@pytest.fixture
def candidate(app):
    return login_client(app, "candidate", 1)


# ------------------------------------------------------------------ service
def test_no_exam_details_is_pending(candidate, monkeypatch):
    _documents(monkeypatch, True)
    result = services.get_eligibility(candidate.user_id)
    assert result == {"status": "Pending", "reason": "Exam details have not been entered yet."}


def test_documents_not_approved_is_pending(candidate, monkeypatch):
    _give_exam_details(candidate.user_id, 1000, "General")
    _documents(monkeypatch, False)
    assert services.get_eligibility(candidate.user_id)["status"] == "Pending"


def test_eligible_with_real_rank_and_approved_documents(candidate, monkeypatch):
    _give_exam_details(candidate.user_id, 1000, "General")
    _documents(monkeypatch, True)
    assert services.get_eligibility(candidate.user_id) == {
        "status": "Eligible", "reason": "Rank 1000 is within the General cut-off of 20000."}


def test_not_eligible_when_rank_is_above_the_cut_off(candidate, monkeypatch):
    _give_exam_details(candidate.user_id, 90000, "General")
    _documents(monkeypatch, True)
    result = services.get_eligibility(candidate.user_id)
    assert result["status"] == "Not Eligible"
    assert result["reason"] == "Rank 90000 is above the General cut-off of 20000."


def test_real_documents_all_approved_is_eligible(candidate):
    _give_exam_details(candidate.user_id, 1000, "General")
    _upload(candidate.user_id, "Approved")
    assert services.get_eligibility(candidate.user_id)["status"] == "Eligible"


def test_real_documents_pending_is_pending(candidate):
    _give_exam_details(candidate.user_id, 1000, "General")
    _upload(candidate.user_id, "Pending")
    assert services.get_eligibility(candidate.user_id)["status"] == "Pending"


def test_real_documents_missing_type_is_pending(candidate):
    _give_exam_details(candidate.user_id, 1000, "General")
    _upload(candidate.user_id, "Approved", kinds=("Marksheet", "ID Proof"))
    assert services.get_eligibility(candidate.user_id)["status"] == "Pending"


def test_no_documents_is_pending_even_with_a_good_rank(candidate):
    _give_exam_details(candidate.user_id, 1000, "General")
    assert services.get_eligibility(candidate.user_id)["status"] == "Pending"


def test_service_can_raise_when_exam_details_are_missing(candidate):
    with pytest.raises(services.ExamDetailsNotEntered):
        services.get_eligibility(candidate.user_id, require_exam_details=True)


# --------------------------------------------------------------- page + API
def test_page_shows_status_and_reason(candidate, monkeypatch):
    _give_exam_details(candidate.user_id, 1000, "General")
    _documents(monkeypatch, True)
    response = candidate.get("/eligibility")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Eligible" in page
    assert "Rank 1000 is within the General cut-off of 20000." in page
    assert "Temporary" not in page


def test_page_shows_pending(candidate, monkeypatch):
    _give_exam_details(candidate.user_id, 1000, "General")
    _documents(monkeypatch, False)
    page = candidate.get("/eligibility").get_data(as_text=True)
    assert "Pending" in page
    assert "Required documents are not all approved yet." in page


def test_json_endpoint(candidate, monkeypatch):
    _give_exam_details(candidate.user_id, 1000, "General")
    _documents(monkeypatch, True)
    response = candidate.get("/api/v1/candidates/me/eligibility")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "Eligible", "reason": "Rank 1000 is within the General cut-off of 20000."}


def test_json_endpoint_without_exam_details_is_422(candidate):
    response = candidate.get("/api/v1/candidates/me/eligibility")
    assert response.status_code == 422
    assert response.get_json()["message"] == "exam details not entered"


def test_page_without_exam_details_still_shows_pending(candidate):
    response = candidate.get("/eligibility")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Pending" in page and "Exam details have not been entered yet." in page


def test_json_endpoint_uses_the_signed_in_candidate_only(app, monkeypatch):
    first = login_client(app, "candidate", 1)
    second = login_client(app, "candidate", 2)
    _give_exam_details(first.user_id, 1000, "General")
    _give_exam_details(second.user_id, 90000, "General")
    _documents(monkeypatch, True)
    assert first.get("/api/v1/candidates/me/eligibility").get_json()["status"] == "Eligible"
    assert second.get("/api/v1/candidates/me/eligibility").get_json()["status"] == "Not Eligible"


def test_anonymous_is_refused(client):
    assert client.get("/api/v1/candidates/me/eligibility").status_code == 401
    page = client.get("/eligibility")
    assert page.status_code == 302
    assert "/accounts/login" in page.headers["Location"]


def test_api_returns_401_after_logout(candidate):
    _give_exam_details(candidate.user_id, 1000, "General")
    assert candidate.get("/api/v1/candidates/me/eligibility").status_code == 200
    assert candidate.post("/accounts/logout").status_code == 204
    assert candidate.get("/api/v1/candidates/me/eligibility").status_code == 401
    assert candidate.get("/eligibility").status_code == 302


def test_administrator_is_refused(app):
    admin = login_client(app, "administrator", 3)
    assert admin.get("/api/v1/candidates/me/eligibility").status_code == 403
    assert admin.get("/eligibility").status_code == 403


def test_pure_decision_code_does_not_import_other_modules():
    folder = pathlib.Path(services.__file__).parent
    pattern = re.compile(r"^\s*(from|import)\s+app\.(accounts|documents)", re.MULTILINE)
    for name in ("evaluation.py", "models.py", "seed.py"):
        assert not pattern.search((folder / name).read_text(encoding="utf-8")), name
