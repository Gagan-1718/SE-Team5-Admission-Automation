from app.accounts.models import ExamRecord, User
from app.accounts.seed import seed
from app.accounts.services import get_exam_details
from app.extensions import db

from .test_registration import registration_payload


def register_and_login(client):
    payload = registration_payload()
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    ).status_code == 200
    return payload


def seed_records(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "fictional-admin-password")
    with app.app_context():
        seed()


def test_valid_exam_details_match_seeded_record_and_copy_rank_category(client, app, monkeypatch):
    seed_records(app, monkeypatch)
    payload = register_and_login(client)

    response = client.put(
        "/accounts/exam-details",
        json={"exam_type": "KCET", "rank": 1000, "category": "General", "score": 185.0},
    )

    assert response.status_code == 200
    assert response.get_json()["exam_details"] == {
        "exam_type": "KCET",
        "rank": 1000,
        "category": "General",
        "score": 185.0,
    }
    assert client.get("/accounts/profile").get_json()["rank"] == 1000
    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == payload["email"])
        ).scalar_one()
        assert user.exam_record_id is not None


def test_ews_exam_record_is_supported(client, app, monkeypatch):
    seed_records(app, monkeypatch)
    payload = register_and_login(client)

    response = client.put(
        "/accounts/exam-details",
        json={"exam_type": "KCET", "rank": 9000, "category": "EWS", "score": 150.0},
    )

    assert response.status_code == 200
    assert response.get_json()["exam_details"]["category"] == "EWS"


def test_invalid_exam_details_return_422_without_changes(client, app, monkeypatch):
    seed_records(app, monkeypatch)
    payload = register_and_login(client)

    response = client.put(
        "/accounts/exam-details",
        json={"exam_type": "KCET", "rank": 1000, "category": "General", "score": 999.0},
    )

    assert response.status_code == 422
    assert response.get_json()["error"] == "no_matching_record"
    assert client.get("/accounts/profile").get_json()["rank"] is None
    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == payload["email"])
        ).scalar_one()
        assert user.exam_record_id is None


def test_anonymous_exam_details_access_is_denied(client):
    response = client.put(
        "/accounts/exam-details",
        json={"exam_type": "KCET", "rank": 1000, "category": "General", "score": 185.0},
    )

    assert response.status_code == 401


def test_seed_is_idempotent_and_creates_administrator(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "fictional-admin-password")
    with app.app_context():
        seed()
        seed()
        assert db.session.execute(db.select(db.func.count(ExamRecord.id))).scalar_one() == 8
        admin = db.session.execute(
            db.select(User).where(User.email == "admin@example.test")
        ).scalar_one()
        assert admin.name == "Fictional Admin"
        assert admin.role == "administrator"
        assert admin.password_hash != "fictional-admin-password"


def test_generated_admin_password_is_printed_once_when_missing(app, monkeypatch, capsys):
    monkeypatch.delenv("ADMIN_SEED_PASSWORD", raising=False)
    with app.app_context():
        seed()
        first_output = capsys.readouterr().out
        seed()
        second_output = capsys.readouterr().out

    assert "Generated ADMIN_SEED_PASSWORD:" in first_output
    assert second_output == ""


def test_get_exam_details_returns_record_or_none(client, app, monkeypatch):
    seed_records(app, monkeypatch)
    payload = register_and_login(client)
    with app.app_context():
        candidate = db.session.execute(
            db.select(User).where(User.email == payload["email"])
        ).scalar_one()
        assert get_exam_details(candidate.id) is None

    client.put(
        "/accounts/exam-details",
        json={"exam_type": "COMEDK", "rank": 800, "category": "General", "score": 190.0},
    )
    with app.app_context():
        candidate = db.session.execute(
            db.select(User).where(User.email == payload["email"])
        ).scalar_one()
        assert get_exam_details(candidate.id) == {
            "exam_type": "COMEDK",
            "rank": 800,
            "category": "General",
            "score": 190.0,
        }
