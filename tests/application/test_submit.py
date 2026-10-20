"""Submission tests (#3 / ADM-F-005 / TC-005). Fictional data only."""
import re

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application import services
from app.application.models import DRAFT, FORM_FIELDS, SUBMITTED, Application
from app.extensions import db

API = "/api/v1/applications"
REFERENCE = re.compile(r"^ADM-\d{4}-\d{6}$")
COMPLETE = {
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


def create(client, data):
    return client.post(API, json=data).get_json()["applicationId"]


# ----------------------------------------------------------- successful submit

def test_complete_application_is_submitted_with_reference_number(client):
    application_id = create(client, COMPLETE)
    response = client.post(f"{API}/{application_id}/submit")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == SUBMITTED
    assert REFERENCE.match(body["referenceNumber"])

    application = stored_application()
    assert application.status == SUBMITTED
    assert application.reference_number == body["referenceNumber"]


def test_submitted_application_is_visible_through_me_endpoint(client):
    application_id = create(client, COMPLETE)
    reference = client.post(f"{API}/{application_id}/submit").get_json()["referenceNumber"]
    body = client.get(f"{API}/me").get_json()
    assert (body["status"], body["referenceNumber"]) == (SUBMITTED, reference)


def test_reference_numbers_are_unique_per_application(client, other_client):
    first_id = create(client, COMPLETE)
    first = client.post(f"{API}/{first_id}/submit").get_json()["referenceNumber"]

    second_id = create(other_client, COMPLETE)
    second = other_client.post(f"{API}/{second_id}/submit").get_json()["referenceNumber"]

    assert first != second


# ------------------------------------------------------- incomplete is rejected

def test_incomplete_application_is_rejected_with_field_level_errors(client):
    application_id = create(client, {"guardian_name": "Fictional Guardian"})
    response = client.post(f"{API}/{application_id}/submit")

    assert response.status_code == 422
    fields = response.get_json()["fields"]
    assert set(fields) == set(FORM_FIELDS) - {"guardian_name"}

    application = stored_application()
    assert application.status == DRAFT
    assert application.reference_number is None


@pytest.mark.parametrize("missing", FORM_FIELDS)
def test_each_mandatory_field_is_required(client, missing):
    data = {name: value for name, value in COMPLETE.items() if name != missing}
    application_id = create(client, data)
    response = client.post(f"{API}/{application_id}/submit")
    assert response.status_code == 422
    assert list(response.get_json()["fields"]) == [missing]


def test_whitespace_only_value_counts_as_missing(client):
    application_id = create(client, {**COMPLETE, "school_name": "   "})
    response = client.post(f"{API}/{application_id}/submit")
    assert response.status_code == 422
    assert "school_name" in response.get_json()["fields"]


def test_draft_can_be_completed_later_and_then_submitted(client):
    application_id = create(client, {"guardian_name": "Fictional Guardian"})
    assert client.post(f"{API}/{application_id}/submit").status_code == 422

    client.put(f"{API}/{application_id}", json=COMPLETE)
    assert client.post(f"{API}/{application_id}/submit").status_code == 200


# ------------------------------------------------------------ no duplicates

def test_submitting_twice_is_rejected_and_keeps_the_first_reference(client):
    application_id = create(client, COMPLETE)
    first = client.post(f"{API}/{application_id}/submit").get_json()["referenceNumber"]

    second = client.post(f"{API}/{application_id}/submit")
    assert second.status_code == 409
    assert stored_application().reference_number == first


def test_stale_second_submit_cannot_overwrite_the_reference(app):
    """Two requests both loaded the same Draft; only the first may submit.

    The second request holds its own session, so its copy still says "Draft" and the
    in-memory check passes. Only the conditional UPDATE can stop it.
    """
    application_id = services.create_draft(1, COMPLETE).id

    with Session(db.engine) as other_request:
        stale = other_request.get(Application, application_id)
        assert stale.is_draft

        services.submit(db.session.get(Application, application_id))  # first request wins
        reference = stored_application().reference_number

        with pytest.raises(services.ApplicationLocked):
            services.submit(stale)

    assert stored_application().reference_number == reference


def test_submitted_application_cannot_be_edited_again(client):
    application_id = create(client, COMPLETE)
    client.post(f"{API}/{application_id}/submit")
    response = client.put(f"{API}/{application_id}", json={"guardian_name": "Changed"})
    assert response.status_code == 409
    assert stored_application().guardian_name == "Fictional Guardian"


# ------------------------------------------------------------------ security

def test_candidate_cannot_submit_another_candidates_application(client, other_client):
    application_id = create(client, COMPLETE)

    assert other_client.post(f"{API}/{application_id}/submit").status_code == 403
    assert stored_application(candidate_id=1).status == DRAFT


def test_submit_unknown_application_is_404(client):
    assert client.post(f"{API}/9999/submit").status_code == 404


# ----------------------------------------------------------------- HTML form

def test_form_submit_shows_reference_number_and_locks_the_form(client):
    response = client.post("/application/submit", data=COMPLETE, follow_redirects=True)
    assert response.status_code == 200

    reference = stored_application().reference_number
    assert REFERENCE.match(reference)
    assert reference.encode() in response.data
    assert b"can no longer be edited" in response.data
    assert b"Save draft" not in response.data


def test_form_submit_with_missing_fields_shows_errors_and_keeps_typed_values(client):
    response = client.post("/application/submit", data={"guardian_name": "Typed Name"})

    assert response.status_code == 422
    assert b"This field is required." in response.data
    assert b"Typed Name" in response.data
    application = stored_application()
    assert application.status == DRAFT
    assert application.guardian_name == "Typed Name"  # kept as a draft


def test_form_submit_with_invalid_value_is_rejected(client):
    data = {**COMPLETE, "percentage": "abc"}
    response = client.post("/application/submit", data=data)
    assert response.status_code == 422
    assert b"Enter a number between 0 and 100." in response.data
    assert stored_application() is None


def test_form_submit_twice_is_rejected(client):
    client.post("/application/submit", data=COMPLETE)
    reference = stored_application().reference_number

    response = client.post("/application/submit", data=COMPLETE)
    assert response.status_code == 409
    assert stored_application().reference_number == reference


# ------------------------------------------------------------ database rules

def test_database_rejects_submitted_without_reference(app):
    db.session.add(Application(candidate_id=1, status=SUBMITTED))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_database_rejects_draft_with_reference(app):
    db.session.add(Application(candidate_id=1, status=DRAFT, reference_number="ADM-2026-000001"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_database_rejects_duplicate_reference_number(app):
    db.session.add(Application(candidate_id=1, status=SUBMITTED, reference_number="ADM-2026-000001"))
    db.session.commit()
    db.session.add(Application(candidate_id=2, status=SUBMITTED, reference_number="ADM-2026-000001"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
