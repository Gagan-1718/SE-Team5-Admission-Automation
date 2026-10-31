from app.accounts.models import User
from app.extensions import db


def registration_payload(**overrides):
    payload = {
        "name": "Fictional Candidate",
        "email": "candidate@example.test",
        "mobile": "9876543210",
        "date_of_birth": "2005-04-12",
        "password": "fictional-password-123",
    }
    payload.update(overrides)
    return payload


def test_valid_registration_persists_candidate_with_hashed_password(client, app):
    response = client.post("/accounts/register", json=registration_payload())

    assert response.status_code == 201
    with app.app_context():
        user = db.session.execute(db.select(User)).scalar_one()
        assert user.name == "Fictional Candidate"
        assert user.role == "candidate"
        assert user.password_hash != "fictional-password-123"
        assert user.password_hash.startswith("scrypt:")


def test_registration_requires_valid_fields(client):
    assert client.post("/accounts/register", json={}).status_code == 400
    assert client.post("/accounts/register", json=registration_payload(email="bad")).status_code == 400
    assert client.post("/accounts/register", json=registration_payload(mobile="123")).status_code == 400
    assert client.post("/accounts/register", json=registration_payload(password="short")).status_code == 400


def test_duplicate_email_and_mobile_are_rejected(client):
    assert client.post("/accounts/register", json=registration_payload()).status_code == 201
    assert client.post(
        "/accounts/register", json=registration_payload(mobile="9876543211")
    ).status_code == 409
    assert client.post(
        "/accounts/register", json=registration_payload(email="other@example.test")
    ).status_code == 409


def test_public_registration_cannot_assign_administrator_role(client, app):
    response = client.post(
        "/accounts/register", json=registration_payload(role="administrator")
    )

    assert response.status_code == 201
    with app.app_context():
        user = db.session.execute(db.select(User)).scalar_one()
        assert user.role == "candidate"

