from app.accounts.seed import seed

from .test_registration import registration_payload


VALID_EXAM = {
    "exam_type": "KCET",
    "rank": 1000,
    "category": "General",
    "score": 185.0,
}


def register_and_login(client):
    payload = registration_payload()
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    ).status_code == 200


def seed_exam_records(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "fictional-admin-password")
    with app.app_context():
        seed()


def test_profile_page_renders_exam_form_choices(client):
    register_and_login(client)

    page = client.get("/accounts/profile-page")
    html = page.get_data(as_text=True)

    assert page.status_code == 200
    assert "Exam details" in html
    assert 'id="exam-details-form"' in html
    assert 'value="KCET"' in html
    assert 'value="COMEDK"' in html
    for category in ("General", "OBC", "SC", "ST", "EWS"):
        assert f'value="{category}"' in html
    assert 'id="exam-details-message"' in html
    assert 'role="alert"' in html


def test_valid_exam_details_are_saved_and_profile_data_persists(client, app, monkeypatch):
    seed_exam_records(app, monkeypatch)
    register_and_login(client)

    response = client.put("/accounts/exam-details", json=VALID_EXAM)
    assert response.status_code == 200
    assert response.get_json()["exam_details"] == {
        "exam_type": "KCET",
        "rank": 1000,
        "category": "General",
        "score": 185.0,
    }

    profile = client.get("/accounts/profile")
    assert profile.get_json()["rank"] == 1000
    assert profile.get_json()["category"] == "General"

    reloaded_page = client.get("/accounts/profile-page").get_data(as_text=True)
    assert "data.rank" in reloaded_page
    assert "data.category" in reloaded_page


def test_non_matching_exam_details_return_visible_error_contract(client, app, monkeypatch):
    seed_exam_records(app, monkeypatch)
    register_and_login(client)

    response = client.put(
        "/accounts/exam-details",
        json={**VALID_EXAM, "score": 999.0},
    )

    assert response.status_code == 422
    assert response.get_json()["error"] == "no_matching_record"
    assert "No matching exam record was found" in response.get_json()["message"]

    page = client.get("/accounts/profile-page").get_data(as_text=True)
    assert "No matching exam record was found" in page
    assert "showMessage(examMessage" in page


def test_anonymous_candidate_cannot_update_exam_details(client):
    response = client.put("/accounts/exam-details", json=VALID_EXAM)
    assert response.status_code == 401
