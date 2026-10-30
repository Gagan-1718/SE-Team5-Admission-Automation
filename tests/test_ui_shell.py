"""Shared shell and friendly error-page coverage."""
import pytest

from app.accounts.models import User
from app.accounts.security import hash_password
from app.extensions import db


PASSWORD = "fictional-password-1"


def logged_in_client(app, role, number):
    email = f"shell.{role}.{number}@example.test"
    db.session.add(User(name=f"Fictional {role}", email=email, mobile=f"90000000{number:02d}", role=role,
                        password_hash=hash_password(PASSWORD)))
    db.session.commit()
    client = app.test_client()
    assert client.post("/accounts/login", json={"identifier": email, "password": PASSWORD}).status_code == 200
    return client


def test_anonymous_home_has_product_story_and_public_actions(client):
    response = client.get("/")
    html = response.data.decode()
    assert response.status_code == 200
    assert "Feature modules are being added in Sprint One" not in html
    assert "From application to seat" in html
    assert 'href="/accounts/login"' in html
    assert 'href="/accounts/register"' in html


def test_error_pages_are_friendly_and_do_not_expose_tracebacks(client):
    response = client.get("/missing-page")
    html = response.data.decode()
    assert response.status_code == 404
    assert "Page not found" in html
    assert "Traceback" not in html
    assert 'href="/"' in html


@pytest.mark.parametrize(
    ("role", "number", "home"),
    (("candidate", 21, "/dashboard"), ("administrator", 22, "/admin/dashboard")),
)
def test_error_page_home_links_follow_authenticated_role(app, role, number, home):
    response = logged_in_client(app, role, number).get("/missing-page")
    assert response.status_code == 404
    assert f'href="{home}"' in response.data.decode()


def test_forbidden_page_is_friendly_for_anonymous_and_admin(app, client):
    with app.test_request_context("/"):
        response = app.make_response(app.handle_http_exception(__import__("werkzeug").exceptions.Forbidden()))
    assert response.status_code == 403
    assert b"Access denied" in response.get_data()
    assert b"Traceback" not in response.get_data()

    admin_response = logged_in_client(app, "administrator", 23).get("/application")
    assert admin_response.status_code == 403
    assert b'href="/admin/dashboard"' in admin_response.data


def test_internal_error_page_is_friendly(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/__test-error")
    def _raise_error():
        raise RuntimeError("secret internal detail")

    for test_client, home in ((client, b'href="/"'),
                              (logged_in_client(app, "candidate", 24), b'href="/dashboard"'),
                              (logged_in_client(app, "administrator", 25), b'href="/admin/dashboard"')):
        response = test_client.get("/__test-error")
        assert response.status_code == 500
        assert b"Something went wrong" in response.get_data()
        assert b"secret internal detail" not in response.get_data()
        assert b"Traceback" not in response.get_data()
        assert home in response.data
