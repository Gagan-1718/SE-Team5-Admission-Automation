"""Fixtures for the application module: two fictional candidates and real logins."""
import pytest

from app.accounts.models import User
from app.accounts.security import hash_password
from app.extensions import db

PASSWORD = "fictional-password-1"


def _identifier(number):
    return f"candidate{number}@example.test"


def login(client, number):
    """Log a test client in as fictional candidate 1 or 2 through the real login route."""
    response = client.post(
        "/accounts/login", json={"identifier": _identifier(number), "password": PASSWORD}
    )
    assert response.status_code == 200, response.get_data(as_text=True)


@pytest.fixture(autouse=True)
def candidate_users(app):
    """Users 1 and 2 exist in every test, so foreign keys to users.id are satisfied."""
    for number in (1, 2):
        db.session.add(
            User(
                name=f"Fictional Candidate {number}",
                email=_identifier(number),
                mobile=f"900000000{number}",
                password_hash=hash_password(PASSWORD),
                role="candidate",
            )
        )
    db.session.commit()


@pytest.fixture
def client(app, candidate_users):
    """A browser logged in as candidate 1 (overrides the shared anonymous client)."""
    test_client = app.test_client()
    login(test_client, 1)
    return test_client


@pytest.fixture
def other_client(app, candidate_users):
    """A separate browser logged in as candidate 2."""
    test_client = app.test_client()
    login(test_client, 2)
    return test_client


@pytest.fixture
def anonymous_client(app):
    return app.test_client()


@pytest.fixture
def admin_client(app):
    """A browser logged in as an administrator (must be refused by candidate pages)."""
    db.session.add(
        User(
            name="Fictional Admin",
            email="admin@example.test",
            mobile="9000000009",
            password_hash=hash_password(PASSWORD),
            role="administrator",
        )
    )
    db.session.commit()
    test_client = app.test_client()
    response = test_client.post(
        "/accounts/login", json={"identifier": "admin@example.test", "password": PASSWORD}
    )
    assert response.status_code == 200
    return test_client
