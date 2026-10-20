from app.accounts.models import User
from app.extensions import db

from .test_registration import registration_payload


def register_candidate(client):
    payload = registration_payload()
    assert client.post("/accounts/register", json=payload).status_code == 201
    return payload


def login(client, identifier, password="fictional-password-123"):
    return client.post(
        "/accounts/login", json={"identifier": identifier, "password": password}
    )


def test_login_accepts_email_and_exposes_identity(client):
    payload = register_candidate(client)

    response = login(client, payload["email"])

    assert response.status_code == 200
    assert response.get_json()["role"] == "candidate"
    assert response.get_json()["user_id"] == 1
    assert client.get("/accounts/me").get_json()["id"] == 1


def test_login_accepts_mobile(client):
    payload = register_candidate(client)

    assert login(client, payload["mobile"]).status_code == 200


def test_invalid_login_uses_generic_error(client):
    payload = register_candidate(client)

    wrong_password = login(client, payload["email"], "wrong-password")
    unknown_user = login(client, "unknown@example.test", "wrong-password")

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.get_json() == unknown_user.get_json()


def test_logout_invalidates_the_server_side_session(client):
    payload = register_candidate(client)
    assert login(client, payload["email"]).status_code == 200
    assert client.get("/accounts/me").status_code == 200

    logout_response = client.post("/accounts/logout")

    assert logout_response.status_code == 204
    assert client.get("/accounts/me").status_code == 401
    with client.application.app_context():
        assert db.session.execute(db.select(User)).scalar_one().sessions == []

