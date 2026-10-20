"""Draft application tests (#2 / ADM-F-004 / TC-004). Fictional data only."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.application import services
from app.application.models import DRAFT, SUBMITTED, Application
from app.extensions import db

from .conftest import login

API = "/api/v1/applications"
VALID = {
    "guardian_name": "Fictional Guardian",
    "guardian_mobile": "9876543210",
    "school_name": "Fictional PU College",
    "board": "CBSE",
    "percentage": 87.5,
}


def stored_application(candidate_id=1):
    db.session.expire_all()
    return db.session.execute(
        db.select(Application).filter_by(candidate_id=candidate_id)
    ).scalar_one_or_none()


# ----------------------------------------------------- save partial draft / resume

def test_partial_draft_is_saved_as_draft_without_reference_number(client):
    response = client.post(API, json={"guardian_name": "Fictional Guardian"})
    assert response.status_code == 201
    assert response.get_json()["status"] == DRAFT

    application = stored_application()
    assert application.status == DRAFT
    assert application.reference_number is None
    assert application.guardian_name == "Fictional Guardian"
    assert application.school_name is None


def test_empty_draft_can_be_created(client):
    assert client.post(API, json={}).status_code == 201


def test_form_save_then_resume_in_a_new_session_shows_saved_values(app, client):
    client.post("/application", data={"guardian_name": "Fictional Guardian", "board": "ICSE"})

    other_session = app.test_client()  # like logging out and back in: nothing but the DB remains
    login(other_session, 1)
    page = other_session.get("/application")
    assert page.status_code == 200
    assert b"Fictional Guardian" in page.data
    assert b'<option value="ICSE" selected>' in page.data


def test_form_save_shows_confirmation_and_keeps_editing_possible(client):
    response = client.post("/application", data={"guardian_name": "First"}, follow_redirects=True)
    assert b"Draft saved" in response.data

    client.post("/application", data={"guardian_name": "Second", "school_name": "Fictional School"})
    application = stored_application()
    assert (application.guardian_name, application.school_name) == ("Second", "Fictional School")
    assert db.session.execute(db.select(db.func.count(Application.id))).scalar() == 1


def test_put_updates_only_the_supplied_fields(client):
    created = client.post(API, json=VALID).get_json()
    response = client.put(f"{API}/{created['applicationId']}", json={"school_name": "Another School"})
    assert response.status_code == 200
    fields = response.get_json()["fields"]
    assert fields["school_name"] == "Another School"
    assert fields["guardian_name"] == "Fictional Guardian"
    assert fields["percentage"] == 87.5


def test_get_me_returns_saved_draft_and_404_when_none(client):
    assert client.get(f"{API}/me").status_code == 404

    client.post(API, json=VALID)
    body = client.get(f"{API}/me").get_json()
    assert body["status"] == DRAFT
    assert body["referenceNumber"] is None
    assert body["fields"] == VALID


def test_blank_text_clears_a_field(client):
    created = client.post(API, json=VALID).get_json()
    client.put(f"{API}/{created['applicationId']}", json={"school_name": "   "})
    assert stored_application().school_name is None


# ----------------------------------------------------------------- validation

@pytest.mark.parametrize(
    "field, value",
    [
        ("guardian_mobile", "12345"),
        ("guardian_mobile", "98765abcde"),
        ("board", "Not A Board"),
        ("percentage", "abc"),
        ("percentage", 101),
        ("percentage", -1),
        ("percentage", "nan"),
        ("guardian_name", "x" * 101),
    ],
)
def test_invalid_field_is_rejected_with_field_error_and_nothing_saved(client, field, value):
    response = client.post(API, json={field: value})
    assert response.status_code == 422
    assert field in response.get_json()["fields"]
    assert stored_application() is None


def test_invalid_update_leaves_saved_draft_unchanged(client):
    created = client.post(API, json=VALID).get_json()
    response = client.put(f"{API}/{created['applicationId']}", json={"percentage": 500, "school_name": "New"})
    assert response.status_code == 422
    application = stored_application()
    assert application.percentage == 87.5
    assert application.school_name == "Fictional PU College"


def test_invalid_form_post_shows_error_and_keeps_typed_values(client):
    response = client.post("/application", data={"guardian_name": "Typed Name", "percentage": "abc"})
    assert response.status_code == 422
    assert b"Enter a number between 0 and 100." in response.data
    assert b"Typed Name" in response.data
    assert stored_application() is None


def test_non_object_json_body_is_rejected(client):
    assert client.post(API, json=["not", "an", "object"]).status_code == 400
    assert client.post(API, data="not json", content_type="text/plain").status_code == 400


def test_user_text_is_escaped_in_the_page(client):
    client.post("/application", data={"guardian_name": "<script>alert(1)</script>"})
    page = client.get("/application")
    assert b"<script>alert(1)</script>" not in page.data
    assert b"&lt;script&gt;" in page.data


# --------------------------------------------------- one per candidate / security

def test_second_application_for_the_same_candidate_is_rejected(client):
    assert client.post(API, json={}).status_code == 201
    response = client.post(API, json={})
    assert response.status_code == 409
    assert response.get_json()["status"] == 409


def test_client_cannot_set_status_candidate_or_reference_number(client):
    client.post(
        API,
        json={"status": SUBMITTED, "candidate_id": 99, "reference_number": "FAKE", "guardian_name": "A"},
    )
    application = stored_application(candidate_id=1)
    assert application is not None
    assert (application.status, application.reference_number) == (DRAFT, None)
    assert stored_application(candidate_id=99) is None


def test_candidate_cannot_edit_another_candidates_application(client, other_client):
    created = client.post(API, json=VALID).get_json()

    response = other_client.put(f"{API}/{created['applicationId']}", json={"guardian_name": "Hijack"})
    assert response.status_code == 403
    assert stored_application(candidate_id=1).guardian_name == "Fictional Guardian"


def test_put_unknown_application_is_404(client):
    assert client.put(f"{API}/9999", json={}).status_code == 404


def test_submitted_application_cannot_be_edited(client):
    created = client.post(API, json=VALID).get_json()
    application = stored_application()
    application.status = SUBMITTED
    application.reference_number = "ADM-TEST-000001"
    db.session.commit()

    api_response = client.put(f"{API}/{created['applicationId']}", json={"guardian_name": "Late edit"})
    form_response = client.post("/application", data={"guardian_name": "Late edit"})

    assert api_response.status_code == 409
    assert form_response.status_code == 409
    assert stored_application().guardian_name == "Fictional Guardian"


# ----------------------------------------------------- service and DB constraints

def test_save_draft_service_creates_then_updates_same_row(app):
    first = services.save_draft(1, {"guardian_name": "One"})
    second = services.save_draft(1, {"guardian_name": "Two"})
    assert first.id == second.id
    assert second.guardian_name == "Two"


def test_database_rejects_unknown_status(app):
    db.session.add(Application(candidate_id=1, status="Approved"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_database_rejects_duplicate_candidate(app):
    db.session.add(Application(candidate_id=1))
    db.session.commit()
    db.session.add(Application(candidate_id=1))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_database_rejects_out_of_range_percentage(app):
    db.session.add(Application(candidate_id=1, percentage=150))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_database_rejects_application_for_unknown_user(app):
    """candidate_id must point at a real row in users (foreign key)."""
    db.session.add(Application(candidate_id=999))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
