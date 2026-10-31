from app.accounts.models import ExamRecord, User
from app.extensions import db

from .test_registration import registration_payload


def register_and_login(client, email="candidate@example.test"):
    payload = registration_payload(email=email)
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login",
        json={"identifier": email, "password": payload["password"]},
    ).status_code == 200


def test_anonymous_dashboard_redirects_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/accounts/login?next=/dashboard" in response.headers["Location"]


def test_candidate_dashboard_has_seven_steps_and_summary(client):
    register_and_login(client)
    response = client.get("/dashboard")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert body.count("step-dot") == 7
    assert "Profile and exam details" in body
    assert "Documents approved" in body
    assert "Enter your exam details to continue." in body


def test_administrator_is_denied_dashboard(client, app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "fictional-admin-password")
    from app.accounts.seed import seed
    with app.app_context():
        seed()
    assert client.post(
        "/accounts/login",
        json={"identifier": "admin@example.test", "password": "fictional-admin-password"},
    ).status_code == 200
    assert client.get("/dashboard").status_code == 403


def test_dashboard_uses_monkeypatched_journey_and_selects_problem_first(client, monkeypatch):
    register_and_login(client)
    fake_steps = [
        {"key": "profile", "label": "Profile and exam details", "state": "current", "detail": "current", "href": "/accounts/profile-page"},
        {"key": "application", "label": "Application", "state": "problem", "detail": "fix this", "href": "/application"},
    ] + [
        {"key": str(i), "label": f"Step {i}", "state": "locked", "detail": "later", "href": "/"}
        for i in range(5)
    ]
    monkeypatch.setattr("app.accounts.routes.all_steps", lambda candidate_id: fake_steps)
    body = client.get("/dashboard").get_data(as_text=True)
    assert "fix this" in body
    assert "Open Application" in body


def test_login_rejects_external_next_but_keeps_local_next(client):
    external = client.get("/accounts/login?next=https://example.test/steal").get_data(as_text=True)
    local = client.get("/accounts/login?next=/application").get_data(as_text=True)
    assert 'https://example.test/steal' not in external
    assert 'const requestedNext = "/application"' in local
