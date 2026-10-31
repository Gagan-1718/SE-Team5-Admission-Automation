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


def test_choice_styles_cover_stacked_and_narrow_layouts():
    css = open("static/css/choices.css", encoding="utf-8").read()
    assert ".choices-layout" in css
    assert "@media (max-width: 900px)" in css
    assert "@media (max-width: 400px)" in css


def test_search_query_is_passed_to_catalogue_service(app, choice_data, monkeypatch):
    captured = {}
    monkeypatch.setattr(routes, "get_eligibility", lambda candidate_id: {
        "status": "Pending", "reason": "Waiting for review."
    })

    def fake_catalogue(query=None):
        captured["query"] = query
        return []

    monkeypatch.setattr(routes, "list_catalogue", fake_catalogue)
    response = _logged_in_client(app, choice_data["candidate_ids"][0]).get("/choices?q=Mechanical")
    assert response.status_code == 200
    assert captured["query"] == "Mechanical"
    assert "No colleges or branches match" in response.get_data(as_text=True)


def test_category_specific_zero_seat_warning_is_rendered(app, choice_data, monkeypatch):
    monkeypatch.setattr(routes, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "Rank is within the cut-off."
    })
    monkeypatch.setattr(routes, "get_exam_details", lambda candidate_id: {"category": "General"})
    page = _logged_in_client(app, choice_data["candidate_ids"][0]).get("/choices").get_data(as_text=True)
    assert "8 General seats left" in page
    assert "0 General seats left" in page
