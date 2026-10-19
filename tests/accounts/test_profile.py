from .test_registration import registration_payload


def register_and_login(client):
    payload = registration_payload()
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    ).status_code == 200
    return payload


def test_profile_can_be_read_and_updated(client):
    register_and_login(client)
    assert client.get("/accounts/profile-page").status_code == 200

    response = client.put(
        "/accounts/profile",
        json={
            "name": "Updated Fictional Candidate",
            "mobile": "9876543211",
            "rank": 1000,
            "category": "General",
        },
    )

    assert response.status_code == 200
    profile = client.get("/accounts/profile")
    assert profile.status_code == 200
    assert profile.get_json()["rank"] == 1000
    assert profile.get_json()["category"] == "General"
    assert profile.get_json()["email"] == "candidate@example.test"
    assert profile.get_json()["role"] == "candidate"


def test_profile_update_rejects_invalid_rank_and_category(client):
    register_and_login(client)

    invalid_rank = client.put(
        "/accounts/profile",
        json={"name": "Candidate", "mobile": "9876543211", "rank": 0, "category": "General"},
    )
    invalid_category = client.put(
        "/accounts/profile",
        json={"name": "Candidate", "mobile": "9876543211", "rank": 1000, "category": "Unknown"},
    )

    assert invalid_rank.status_code == 400
    assert invalid_category.status_code == 400


def test_profile_changes_persist_after_logout_and_login(client):
    payload = register_and_login(client)
    assert client.put(
        "/accounts/profile",
        json={"name": "Persisted Candidate", "mobile": payload["mobile"], "rank": 42, "category": "OBC"},
    ).status_code == 200
    assert client.post("/accounts/logout").status_code == 204
    assert client.post(
        "/accounts/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    ).status_code == 200

    profile = client.get("/accounts/profile").get_json()
    assert profile["name"] == "Persisted Candidate"
    assert profile["rank"] == 42
    assert profile["category"] == "OBC"

