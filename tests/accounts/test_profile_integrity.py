from datetime import date, timedelta

from app.accounts.seed import seed
from app.application.models import Application, SUBMITTED
from app.accounts.models import User
from app.extensions import db
from sqlalchemy import inspect, text

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


def test_registration_page_exposes_required_dob_and_api_persists_it(client, app):
    page = client.get("/accounts/register")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert '<label for="date_of_birth">Date of birth</label>' in html
    assert 'name="date_of_birth"' in html
    assert 'type="date"' in html
    assert 'name="date_of_birth" type="date"' in html
    assert 'required>' in html
    assert 'max="' in html
    payload = registration_payload(email="dob@example.test", date_of_birth="2004-02-29")
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 201
    with app.app_context():
        user = db.session.execute(db.select(User).where(User.email == payload["email"])).scalar_one()
        assert user.date_of_birth == date(2004, 2, 29)
    assert client.post("/accounts/login", json={"identifier": payload["email"], "password": payload["password"]}).status_code == 200
    assert client.get("/accounts/profile").get_json()["date_of_birth"] == "2004-02-29"


def test_profile_column_upgrade_preserves_old_candidate_and_is_idempotent(app):
    from app.accounts.seed import _ensure_profile_columns

    with app.app_context():
        db.drop_all()
        db.session.execute(text("CREATE TABLE exam_records (id INTEGER PRIMARY KEY, exam_type VARCHAR(20) NOT NULL, rank INTEGER NOT NULL, category VARCHAR(20) NOT NULL, score FLOAT NOT NULL)"))
        db.session.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(120) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE, mobile VARCHAR(20) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, role VARCHAR(30) NOT NULL)"))
        db.session.execute(text("INSERT INTO users (id, name, email, mobile, password_hash, role) VALUES (7, 'Legacy Candidate', 'legacy@example.test', '9000000007', 'scrypt:legacy', 'candidate')"))
        db.session.commit()

        _ensure_profile_columns()
        _ensure_profile_columns()

        columns = {column["name"] for column in inspect(db.engine).get_columns("users")}
        assert {"exam_record_id", "date_of_birth", "address_line", "city", "pincode"} <= columns
        row = db.session.execute(text("SELECT id, name, email, mobile, password_hash, role FROM users WHERE id = 7")).mappings().one()
        assert dict(row) == {
            "id": 7,
            "name": "Legacy Candidate",
            "email": "legacy@example.test",
            "mobile": "9000000007",
            "password_hash": "scrypt:legacy",
            "role": "candidate",
        }


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
