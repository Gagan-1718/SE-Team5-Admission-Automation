"""An application cannot be submitted until exam details are entered (decision D2-02).

Eligibility needs the rank and category that come from the seeded exam record, so a
submitted application without them would be stuck. Saving a draft is still allowed.
"""
import pytest

from app.accounts.models import User
from app.accounts.security import hash_password
from app.application.models import DRAFT, Application
from app.extensions import db

from .conftest import PASSWORD

API = "/api/v1/applications"
COMPLETE = {
    "guardian_name": "Fictional Guardian",
    "guardian_mobile": "9876543210",
    "school_name": "Fictional PU College",
    "board": "CBSE",
    "percentage": 88.5,
}


@pytest.fixture
def no_exam_client(app):
    """A candidate who has registered but has not entered exam details yet."""
    db.session.add(User(name="Fictional No Exam", email="noexam@example.test", mobile="9000000003",
                        password_hash=hash_password(PASSWORD), role="candidate"))
    db.session.commit()
    client = app.test_client()
    response = client.post("/accounts/login", json={"identifier": "noexam@example.test", "password": PASSWORD})
    assert response.status_code == 200
    return client


def test_draft_can_still_be_saved_without_exam_details(no_exam_client):
    assert no_exam_client.post(API, json={"guardian_name": "Fictional Guardian"}).status_code == 201


def test_api_submit_without_exam_details_is_refused_and_stays_draft(no_exam_client):
    application_id = no_exam_client.post(API, json=COMPLETE).get_json()["applicationId"]
    response = no_exam_client.post(f"{API}/{application_id}/submit")
    assert response.status_code == 422
    assert "exam_details" in response.get_json()["fields"]
    application = db.session.get(Application, application_id)
    assert application.status == DRAFT and application.reference_number is None


def test_page_submit_without_exam_details_explains_and_links_to_profile(no_exam_client):
    response = no_exam_client.post("/application/submit", data=COMPLETE)
    assert response.status_code == 422
    assert b"Enter your exam details on your profile before you submit." in response.data
    assert b'href="/accounts/profile-page"' in response.data


def test_page_warns_before_submitting_when_exam_details_are_missing(no_exam_client):
    page = no_exam_client.get("/application")
    assert b"Enter your exam details first" in page.data


def test_page_has_no_warning_once_exam_details_are_entered(client):
    page = client.get("/application")
    assert b"Enter your exam details first" not in page.data


def test_submit_works_once_exam_details_are_entered(client):
    application_id = client.post(API, json=COMPLETE).get_json()["applicationId"]
    assert client.post(f"{API}/{application_id}/submit").status_code == 200
