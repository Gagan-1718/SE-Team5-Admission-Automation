from app.accounts.models import User
from app.accounts.security import hash_password
from app.extensions import db

from .test_registration import registration_payload


def register_and_login(client):
    payload = registration_payload()
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    ).status_code == 200


def test_anonymous_users_are_denied_protected_page_and_api(client):
    assert client.get("/accounts/dashboard").status_code == 401
    assert client.get("/accounts/me").status_code == 401
    assert client.get("/accounts/admin-check").status_code == 401


def test_candidate_is_denied_administrator_route(client):
    register_and_login(client)

    assert client.get("/accounts/admin-check").status_code == 403


def test_administrator_role_is_checked_from_server_side_account(client, app):
    with app.app_context():
        administrator = User(
            name="Fictional Administrator",
            email="admin@example.test",
            mobile="9000000000",
            password_hash=hash_password("admin-password-123"),
            role="administrator",
        )
        db.session.add(administrator)
        db.session.commit()

    assert client.post(
        "/accounts/login",
        json={"identifier": "admin@example.test", "password": "admin-password-123"},
    ).status_code == 200
    assert client.get("/accounts/admin-check").status_code == 200


def test_identity_contract_is_server_derived(client, app):
    register_and_login(client)
    with app.app_context():
        user = db.session.execute(db.select(User)).scalar_one()
        user.rank = 321
        user.category = "General"
        db.session.commit()

    identity = client.get("/accounts/me").get_json()

    assert identity == {
        "id": 1,
        "role": "candidate",
        "rank": 321,
        "category": "General",
        "name": "Fictional Candidate",
    }

