"""The application step on the candidate dashboard (journey contract, section 4.4)."""
from app.accounts.models import User
from app.application import services
from app.application.journey import step_statuses
from app.extensions import db
from app.journey import CURRENT, DONE, LOCKED

COMPLETE = {"guardian_name": "Fictional Guardian", "guardian_mobile": "9876543210",
            "school_name": "Fictional PU College", "board": "CBSE", "percentage": 88.5}


def only_step(candidate_id):
    steps = step_statuses(candidate_id)
    assert len(steps) == 1 and steps[0]["key"] == "application"
    return steps[0]


def no_exam_candidate():
    user = User(name="Fictional No Exam", email="journey.noexam@example.test", mobile="9000000004",
                password_hash="not-a-real-hash", role="candidate")
    db.session.add(user)
    db.session.commit()
    return user.id


def test_locked_until_exam_details_are_entered():
    step = only_step(no_exam_candidate())
    assert step["state"] == LOCKED and "exam details" in step["detail"]


def test_a_draft_without_exam_details_says_what_is_missing():
    candidate_id = no_exam_candidate()
    services.save_draft(candidate_id, {"guardian_name": "Fictional Guardian"})
    step = only_step(candidate_id)
    assert step["state"] == CURRENT and "exam details" in step["detail"]


def test_current_when_not_started_and_exam_details_exist():
    step = only_step(1)
    assert step["state"] == CURRENT and step["detail"] == "Start your application."


def test_current_while_draft():
    services.save_draft(1, {"guardian_name": "Fictional Guardian"})
    assert only_step(1)["state"] == CURRENT


def test_done_with_reference_once_submitted():
    application = services.save_draft(1, COMPLETE)
    services.submit(application)
    step = only_step(1)
    assert step["state"] == DONE and application.reference_number in step["detail"]
    assert step["href"] == "/application"
