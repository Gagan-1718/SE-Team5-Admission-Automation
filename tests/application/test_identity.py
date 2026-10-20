"""The application module uses the real login (#2 / #3 with accounts #17, #19)."""
import pytest

from app.application.models import Application
from app.extensions import db

from .conftest import login

API = "/api/v1/applications"
VALID = {
    "guardian_name": "Fictional Guardian",
    "guardian_mobile": "9876543210",
    "school_name": "Fictional PU College",
    "board": "CBSE",
    "percentage": 87.5,
}


def stored(candidate_id):
    db.session.expire_all()
    return db.session.execute(
        db.select(Application).filter_by(candidate_id=candidate_id)
    ).scalar_one_or_none()


# ------------------------------------------------------------------ anonymous

@pytest.mark.parametrize("method, path", [("get", "/application"), ("post", "/application"),
                                          ("post", "/application/submit")])
def test_anonymous_pages_redirect_to_login(anonymous_client, method, path):
    response = getattr(anonymous_client, method)(path)
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/accounts/login?next={path}")


@pytest.mark.parametrize("method, path", [("post", API), ("put", f"{API}/1"),
                                          ("get", f"{API}/me"), ("post", f"{API}/1/submit")])
def test_anonymous_api_gets_401(anonymous_client, method, path):
    response = getattr(anonymous_client, method)(path, json={})
    assert response.status_code == 401
    assert response.get_json()["status"] == 401


def test_anonymous_request_changes_nothing(anonymous_client):
    anonymous_client.post("/application", data=VALID)
    anonymous_client.post(API, json=VALID)
    assert db.session.execute(db.select(db.func.count(Application.id))).scalar() == 0


# ------------------------------------------------------------- administrator

def test_administrator_is_refused_on_pages_and_api(admin_client):
    assert admin_client.get("/application").status_code == 403
    assert admin_client.post("/application", data=VALID).status_code == 403
    assert admin_client.post(API, json=VALID).status_code == 403
    assert admin_client.get(f"{API}/me").status_code == 403
    assert db.session.execute(db.select(db.func.count(Application.id))).scalar() == 0


# --------------------------------------------------------- real candidate id

def test_draft_is_saved_under_the_logged_in_candidate(client, other_client):
    other_client.post(API, json={"guardian_name": "Second Candidate Guardian"})

    assert stored(1) is None
    assert stored(2).guardian_name == "Second Candidate Guardian"


def test_each_candidate_sees_only_their_own_draft(client, other_client):
    client.post(API, json={"guardian_name": "First Guardian"})
    other_client.post(API, json={"guardian_name": "Second Guardian"})

    assert client.get(f"{API}/me").get_json()["fields"]["guardian_name"] == "First Guardian"
    assert other_client.get(f"{API}/me").get_json()["fields"]["guardian_name"] == "Second Guardian"
    page = client.get("/application")
    assert b"First Guardian" in page.data and b"Second Guardian" not in page.data


def test_client_cannot_choose_the_candidate_id(client):
    client.post(API, json={"candidate_id": 2, "guardian_name": "Spoof"})
    assert stored(2) is None
    assert stored(1).guardian_name == "Spoof"


# ------------------------------------------- the acceptance criterion of #2

def test_draft_survives_logout_and_login(app, client):
    """TC-004: saved details remain after logging out and logging in."""
    client.post("/application", data={"guardian_name": "Fictional Guardian", "board": "ICSE"})

    assert client.post("/accounts/logout").status_code == 204
    assert client.get("/application").status_code == 302  # logged out: sent to login

    login(client, 1)
    page = client.get("/application")
    assert page.status_code == 200
    assert b"Fictional Guardian" in page.data
    assert b'<option value="ICSE" selected>' in page.data

    client.post("/application", data={"guardian_name": "Edited After Login"})  # can keep editing
    assert stored(1).guardian_name == "Edited After Login"


def test_old_session_cookie_stops_working_after_logout(app, client):
    cookie = client.get_cookie("team5_session").value
    client.post("/accounts/logout")

    thief = app.test_client()
    thief.set_cookie("team5_session", cookie)
    assert thief.get(f"{API}/me").status_code == 401
    assert thief.get("/application").status_code == 302


def test_submitted_reference_is_shown_after_login_again(client):
    client.post("/application/submit", data=VALID)
    reference = stored(1).reference_number
    client.post("/accounts/logout")
    login(client, 1)

    assert reference.encode() in client.get("/application").data
    assert client.get(f"{API}/me").get_json()["referenceNumber"] == reference
