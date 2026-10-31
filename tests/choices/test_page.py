from app.accounts.auth import create_session
from app.accounts.models import User
from app.choices import routes
from app.extensions import db


def _logged_in_client(app, user_id):
    client = app.test_client()
    with app.app_context():
        client.set_cookie("team5_session", create_session(db.session.get(User, user_id)))
    return client


def test_anonymous_visitor_is_sent_to_login(client):
    response = client.get("/choices")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/accounts/login?next=/choices")


def test_administrator_receives_forbidden_response(app):
    with app.app_context():
        admin = User(
            name="Fictional Choices Admin",
            email="choices-admin@example.test",
            mobile="9000000012",
            password_hash="test-hash",
            role="administrator",
        )
        db.session.add(admin)
        db.session.commit()
        client = _logged_in_client(app, admin.id)
    assert client.get("/choices").status_code == 403


def test_candidate_page_renders_catalogue_and_eligibility_explanation(app, choice_data, monkeypatch):
    candidate_id = choice_data["candidate_ids"][0]
    monkeypatch.setattr(routes, "get_eligibility", lambda candidate_id: {
        "status": "Pending", "reason": "Documents are still being reviewed."
    })
    response = _logged_in_client(app, candidate_id).get("/choices?q=Computer")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Documents are still being reviewed." in page
    assert "View eligibility" in page
    assert "Fictional Institute" in page
    assert "Computer Science" in page
    assert 'name="q"' in page
    assert 'value="Computer"' in page
    assert 'data-branch-id="' in page
    assert 'disabled' in page
