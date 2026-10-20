from flask import g

from app.accounts.auth import current_candidate_id
from app.accounts.models import User
from app.accounts.security import hash_password
from app.extensions import db

from .test_registration import registration_payload


def login_candidate(client):
    payload = registration_payload()
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    ).status_code == 200


def test_current_candidate_id_is_none_for_anonymous_and_candidate_id_for_candidate(client):
    with client.application.test_request_context():
        g.current_user = None
        assert current_candidate_id() is None
    login_candidate(client)
    with client.application.test_request_context():
        g.current_user = db.session.get(User, 1)
        assert current_candidate_id() == 1


def test_current_candidate_id_is_none_for_administrator(client, app):
    with app.app_context():
        db.session.add(
            User(
                name="Fictional Administrator",
                email="administrator@example.test",
                mobile="9000000001",
                password_hash=hash_password("administrator-password"),
                role="administrator",
            )
        )
        db.session.commit()
    assert client.post(
        "/accounts/login",
        json={"identifier": "administrator@example.test", "password": "administrator-password"},
    ).status_code == 200
    with app.test_request_context():
        g.current_user = db.session.get(User, 1)
        assert current_candidate_id() is None


def test_anonymous_profile_page_redirects_to_login_with_next(client):
    response = client.get("/accounts/profile-page")

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/accounts/login?next=/accounts/profile-page"
    )
