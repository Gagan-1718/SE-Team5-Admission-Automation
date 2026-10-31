"""Accounts integration checks using fictional candidates and administrator data."""

from app.accounts.seed import seed
from app.accounts.models import ExamRecord, User
from app.application.models import Application
from app.documents.models import Document
from app.extensions import db


PASSWORD = "fictional-password-123"
ADMIN_PASSWORD = "fictional-admin-password-123"
APPLICATION_API = "/api/v1/applications"


def candidate_payload(label):
    return {
        "name": f"Fictional Candidate {label}",
        "email": f"candidate-{label.lower()}@example.test",
        "mobile": "9000000001" if label == "A" else "9000000002",
        "password": PASSWORD,
    }


def register(client, label):
    payload = candidate_payload(label)
    response = client.post("/accounts/register", json=payload)
    assert response.status_code == 201, response.get_data(as_text=True)
    return payload, response.get_json()["user_id"]


def login(client, payload):
    response = client.post(
        "/accounts/login",
        json={"identifier": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200, response.get_data(as_text=True)


def seed_admin(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", ADMIN_PASSWORD)
    with app.app_context():
        seed()


def enter_exam_details(client):
    """Use a seeded exam record, as a real candidate must before submitting (D2-02)."""
    if db.session.execute(db.select(ExamRecord).filter_by(exam_type="KCET", rank=1000)).scalar_one_or_none() is None:
        db.session.add(ExamRecord(exam_type="KCET", rank=1000, category="General", score=185.0))
        db.session.commit()
    response = client.put(
        "/accounts/exam-details",
        json={"exam_type": "KCET", "rank": 1000, "category": "General", "score": 185.0},
    )
    assert response.status_code == 200, response.get_data(as_text=True)


def complete_application(client):
    enter_exam_details(client)
    response = client.post(
        APPLICATION_API,
        json={
            "guardian_name": "Fictional Guardian",
            "guardian_mobile": "9111111111",
            "school_name": "Fictional College",
            "board": "CBSE",
            "percentage": 87.5,
        },
    )
    assert response.status_code == 201, response.get_data(as_text=True)
    application_id = response.get_json()["applicationId"]
    response = client.post(f"{APPLICATION_API}/{application_id}/submit")
    assert response.status_code == 200, response.get_data(as_text=True)
    return application_id


def test_candidate_a_cannot_read_or_edit_candidate_b_records(app):
    candidate_a = app.test_client()
    candidate_b = app.test_client()
    payload_a, candidate_a_id = register(candidate_a, "A")
    payload_b, candidate_b_id = register(candidate_b, "B")
    login(candidate_a, payload_a)
    login(candidate_b, payload_b)

    application_b_id = complete_application(candidate_b)
    application_a_id = complete_application(candidate_a)

    with app.app_context():
        document_b = Document(
            candidate_id=candidate_b_id,
            application_id=application_b_id,
            document_type="marksheet",
            stored_name="candidate-b-marksheet.pdf",
        )
        db.session.add(document_b)
        db.session.commit()
        document_b_id = document_b.id

    own_application = candidate_a.get(f"{APPLICATION_API}/me")
    assert own_application.status_code == 200
    assert own_application.get_json()["applicationId"] == application_a_id
    assert b"Fictional Candidate B" not in candidate_a.get("/application").data

    edit_other_application = candidate_a.put(
        f"{APPLICATION_API}/{application_b_id}",
        json={"guardian_name": "Unauthorized change"},
    )
    assert edit_other_application.status_code == 403

    documents_page = candidate_a.get("/documents")
    assert documents_page.status_code == 200
    assert b"candidate-b-marksheet.pdf" not in documents_page.data

    resubmit_other_document = candidate_a.post(
        f"/documents/{document_b_id}/resubmit",
        data={"csrf_token": "not-used-after-ownership-check"},
    )
    assert resubmit_other_document.status_code == 404


def test_logout_invalidates_old_cookie_on_application_and_documents(app):
    client = app.test_client()
    payload, _ = register(client, "A")
    login(client, payload)
    old_cookie = client.get_cookie("team5_session").value

    assert client.post("/accounts/logout").status_code == 204

    stale = app.test_client()
    stale.set_cookie("team5_session", old_cookie)
    assert stale.get(f"{APPLICATION_API}/me").status_code == 401
    assert stale.get("/documents").status_code == 302


def test_anonymous_requests_are_denied_on_discovered_protected_routes(client):
    protected_requests = [
        ("get", "/accounts/me", 401),
        ("get", "/accounts/dashboard", 401),
        ("get", "/accounts/profile", 401),
        ("get", "/accounts/admin-check", 401),
        ("get", "/accounts/profile-page", 302),
        ("post", "/accounts/logout", 401),
        ("get", "/application", 302),
        ("post", "/application", 302),
        ("post", "/application/submit", 302),
        ("post", APPLICATION_API, 401),
        ("put", f"{APPLICATION_API}/1", 401),
        ("get", f"{APPLICATION_API}/me", 401),
        ("post", f"{APPLICATION_API}/1/submit", 401),
        ("get", "/documents/upload", 302),
        ("get", "/documents", 302),
        ("post", "/documents/1/resubmit", 302),
        ("get", "/eligibility", 302),
        ("get", "/api/v1/candidates/me/eligibility", 401),
        ("get", "/admin/colleges", 401),
        ("get", "/admin/documents", 401),
        ("get", "/admin/dashboard", 401),
        ("get", "/admin/audit-logs", 401),
    ]

    for method, path, expected_status in protected_requests:
        response = getattr(client, method)(path, json={} if method in {"post", "put"} else None)
        assert response.status_code == expected_status, f"{method.upper()} {path}"


def test_logout_invalidates_old_cookie_on_eligibility_api(app):
    client = app.test_client()
    payload, _ = register(client, "A")
    login(client, payload)
    old_cookie = client.get_cookie("team5_session").value

    assert client.post("/accounts/logout").status_code == 204

    stale = app.test_client()
    stale.set_cookie("team5_session", old_cookie)
    response = stale.get("/api/v1/candidates/me/eligibility")
    assert response.status_code == 401


def test_anonymous_and_candidate_admin_authorization(app, client, monkeypatch):
    seed_admin(app, monkeypatch)
    admin_paths = (
        "/admin/colleges",
        "/admin/documents",
        "/admin/dashboard",
        "/admin/audit-logs",
    )
    for path in admin_paths:
        assert client.get(path).status_code == 401

    candidate = app.test_client()
    payload, _ = register(candidate, "A")
    login(candidate, payload)
    for path in admin_paths:
        assert candidate.get(path).status_code == 403

    administrator = app.test_client()
    administrator.post(
        "/accounts/login",
        json={"identifier": "admin@example.test", "password": ADMIN_PASSWORD},
    )
    assert administrator.get("/admin/documents").status_code == 200
    assert administrator.get("/admin/colleges").status_code == 200
    assert administrator.get("/admin/dashboard").status_code == 200
    assert administrator.get("/admin/audit-logs").status_code == 200


def test_duplicate_email_and_mobile_are_rejected(client):
    first = candidate_payload("A")
    assert client.post("/accounts/register", json=first).status_code == 201
    duplicate_email = {**candidate_payload("B"), "email": first["email"], "mobile": "9000000003"}
    duplicate_mobile = {**candidate_payload("B"), "email": "other@example.test", "mobile": first["mobile"]}
    assert client.post("/accounts/register", json=duplicate_email).status_code == 409
    assert client.post("/accounts/register", json=duplicate_mobile).status_code == 409


def test_users_store_only_password_hashes(client, app):
    payload, _ = register(client, "A")
    with app.app_context():
        user = db.session.execute(
            db.select(User).where(User.email == payload["email"])
        ).scalar_one()
        row_values = [getattr(user, column.name) for column in User.__table__.columns]
        assert user.password_hash != payload["password"]
        assert payload["password"] not in row_values
        assert user.password_hash.startswith("scrypt:")
