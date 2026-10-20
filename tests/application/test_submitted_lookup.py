"""get_submitted_application: used by the documents module to find the application to attach to."""
from app.application import services
from app.application.models import SUBMITTED
from app.extensions import db

COMPLETE = {
    "guardian_name": "Fictional Guardian",
    "guardian_mobile": "9876543210",
    "school_name": "Fictional PU College",
    "board": "CBSE",
    "percentage": 87.5,
}


def test_no_application_gives_none(app):
    assert services.get_submitted_application(1) is None


def test_draft_is_not_returned(app):
    services.create_draft(1, COMPLETE)
    assert services.get_submitted_application(1) is None


def test_submitted_application_is_returned_with_reference(app):
    application = services.create_draft(1, COMPLETE)
    services.submit(application)

    found = services.get_submitted_application(1)
    assert found.id == application.id
    assert found.status == SUBMITTED
    assert found.reference_number.startswith("ADM-")


def test_other_candidates_application_is_not_returned(app):
    services.submit(services.create_draft(1, COMPLETE))
    assert services.get_submitted_application(2) is None
    db.session.rollback()
