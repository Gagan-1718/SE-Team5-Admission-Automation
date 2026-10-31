from datetime import date, timedelta

from app.accounts.seed import seed
from app.application.models import Application, SUBMITTED
from app.accounts.models import User
from app.extensions import db

from .test_registration import registration_payload


def register_and_login(client, **overrides):
    payload = registration_payload(**overrides)
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login", json={"identifier": payload["email"], "password": payload["password"]}
    ).status_code == 200
    return payload


def test_registration_requires_real_past_date_of_birth(client):
    base = registration_payload()
    for value in (None, "not-a-date", date.today().isoformat(), (date.today() + timedelta(days=1)).isoformat()):
        assert client.post("/accounts/register", json={**base, "date_of_birth": value}).status_code == 400
    assert client.post("/accounts/register", json=base).status_code == 201


def test_address_is_saved_and_pincode_is_validated(client):
    register_and_login(client)
    response = client.put("/accounts/profile", json={
        "name": "Fictional Candidate", "mobile": "9876543210",
        "address_line": "12 Fictional Road", "city": "Bengaluru", "pincode": "560001",
    })
    assert response.status_code == 200
    assert client.get("/accounts/profile").get_json()["pincode"] == "560001"
    assert client.put("/accounts/profile", json={
        "name": "Fictional Candidate", "mobile": "9876543210", "pincode": "1234",
    }).status_code == 400


def test_exam_details_are_locked_after_submission(client, app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "fictional-admin-password")
    with app.app_context():
        seed()
    register_and_login(client)
    assert client.put("/accounts/exam-details", json={
        "exam_type": "KCET", "rank": 1000, "category": "General", "score": 185.0,
    }).status_code == 200
    with app.app_context():
        candidate = db.session.execute(db.select(User).where(User.role == "candidate")).scalar_one()
        db.session.add(Application(
            candidate_id=candidate.id, status=SUBMITTED, reference_number="ADM-2026-000001",
        ))
        db.session.commit()
    response = client.put("/accounts/exam-details", json={
        "exam_type": "KCET", "rank": 4500, "category": "OBC", "score": 160.5,
    })
    assert response.status_code == 409
    assert response.get_json()["message"] == "Exam details are locked after you submit your application"
    page = client.get("/accounts/profile-page").get_data(as_text=True)
    assert "Exam details are locked after you submit your application" in page
    assert 'id="save-exam-details" disabled' in page
