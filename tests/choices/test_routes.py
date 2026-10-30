import pytest

from app.accounts.auth import create_session
from app.accounts.models import User
from app.choices import services
from app.choices.services import add_choice
from app.extensions import db


@pytest.fixture
def eligible(monkeypatch):
    monkeypatch.setattr(services, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "fictional test eligibility"
    })


def _client_for(app, user_id):
    client = app.test_client()
    with app.app_context():
        user = db.session.get(User, user_id)
        client.set_cookie("team5_session", create_session(user))
    return client


def test_anonymous_choice_api_requests_require_authentication(app):
    client = app.test_client()
    assert client.get("/api/v1/choices").status_code == 401
    assert client.post("/api/v1/choices", json={"branchId": 1}).status_code == 401
    assert client.put("/api/v1/choices/order", json={"orderedChoiceIds": []}).status_code == 401
    assert client.post("/api/v1/choices/lock").status_code == 401


def test_administrator_is_forbidden_from_choice_api(app, choice_data):
    with app.app_context():
        admin = User(name="Fictional Admin", email="choice-admin@example.test",
                     mobile="9000000011", password_hash="test-hash", role="administrator")
        db.session.add(admin)
        db.session.commit()
        client = _client_for(app, admin.id)
    assert client.get("/api/v1/choices").status_code == 403


def test_candidate_can_add_and_preview_choice(app, choice_data, eligible):
    client = _client_for(app, choice_data["candidate_ids"][0])
    response = client.post("/api/v1/choices", json={
        "collegeId": choice_data["college_ids"][0],
        "branchId": choice_data["branch_ids"][0],
    })
    assert response.status_code == 201
    body = response.get_json()
    assert body["choice"]["college"] == "Fictional Institute"
    assert client.get("/api/v1/choices").get_json()["locked"] is False


def test_api_rejects_duplicate_and_wrong_college(app, choice_data, eligible):
    client = _client_for(app, choice_data["candidate_ids"][0])
    payload = {"collegeId": choice_data["college_ids"][0], "branchId": choice_data["branch_ids"][0]}
    assert client.post("/api/v1/choices", json=payload).status_code == 201
    duplicate = client.post("/api/v1/choices", json=payload)
    assert duplicate.status_code == 409
    wrong_college = client.post("/api/v1/choices", json={
        "collegeId": choice_data["college_ids"][1], "branchId": choice_data["branch_ids"][0]
    })
    assert wrong_college.status_code == 404


def test_api_preserves_candidate_ownership_and_locking(app, choice_data, eligible):
    first, second = choice_data["candidate_ids"]
    with app.app_context():
        foreign_id = add_choice(second, choice_data["branch_ids"][0]).id
    first_client = _client_for(app, first)
    assert first_client.delete(f"/api/v1/choices/{foreign_id}").status_code == 404
    created = first_client.post("/api/v1/choices", json={"branchId": choice_data["branch_ids"][1]}).get_json()
    assert first_client.post("/api/v1/choices/lock").status_code == 200
    assert first_client.post("/api/v1/choices/lock").status_code == 409
    assert first_client.post("/api/v1/choices", json={"branchId": choice_data["branch_ids"][2]}).status_code == 409
    assert first_client.delete(f"/api/v1/choices/{created['choice']['id']}").status_code == 409


def test_empty_lock_has_contract_status(app, choice_data):
    client = _client_for(app, choice_data["candidate_ids"][0])
    response = client.post("/api/v1/choices/lock")
    assert response.status_code == 422
    assert response.get_json()["message"] == "Add at least one choice first"
