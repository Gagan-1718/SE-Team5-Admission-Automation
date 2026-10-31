"""Central CSRF checks enabled explicitly, including real application forms."""
from html.parser import HTMLParser

import pytest
from flask import jsonify

from app.accounts.models import User
from app.accounts.security import hash_password
from app.application.models import Application
from app.catalogue.models import Branch, College
from app.catalogue.seed import seed
from app.documents.models import Document
from app.extensions import db
from app.security import CSRF_SESSION_KEY, csrf_protection_enabled, csrf_token


class Forms(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.token = None
        self.forms = []
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name") == "csrf-token":
            self.token = attrs.get("content")
        if tag == "form":
            self.current = {"method": attrs.get("method", "get").lower(), "tokens": []}
            self.forms.append(self.current)
        if tag == "input" and self.current is not None and attrs.get("name") == "csrf_token":
            self.current["tokens"].append(attrs.get("value"))

    def handle_endtag(self, tag):
        if tag == "form":
            self.current = None


@pytest.fixture
def protected(app):
    app.config["CSRF_ENABLED"] = True
    app.csrf_writes = []

    @app.route("/_csrf/write", methods=["POST", "PUT", "PATCH", "DELETE", "GET", "HEAD"])
    def write():
        from flask import request
        if request.method not in ("GET", "HEAD"):
            app.csrf_writes.append(request.method)
        return jsonify(ok=True)

    return app


def token(client, path="/accounts/login"):
    response = client.get(path)
    assert response.status_code == 200
    value = Forms(response.get_data(as_text=True)).token
    assert value
    return value


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("supplied", [None, "", "wrong", "non-ascii-☃"])
def test_missing_or_invalid_header_blocks_all_writes(protected, method, supplied):
    client = protected.test_client()
    token(client)
    headers = {} if supplied is None else {"X-CSRF-Token": supplied}
    response = client.open("/_csrf/write", method=method, json={}, headers=headers)
    assert response.status_code == 400
    assert response.json["error"] == "csrf_failed"
    assert "Reload" in response.json["message"]
    assert protected.csrf_writes == []


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_correct_header_allows_each_write_method(protected, method):
    client = protected.test_client()
    value = token(client)
    assert client.open("/_csrf/write", method=method, json={},
                       headers={"X-CSRF-Token": value}).status_code == 200
    assert protected.csrf_writes == [method]


def test_hidden_field_works_but_json_body_token_is_not_a_header(protected):
    client = protected.test_client()
    value = token(client)
    assert client.post("/_csrf/write", data={"csrf_token": value}).status_code == 200
    assert client.post("/_csrf/write", json={"csrf_token": value}).status_code == 400
    assert protected.csrf_writes == ["POST"]


def test_wrong_header_cannot_be_hidden_by_valid_form_token(protected):
    client = protected.test_client()
    value = token(client)
    assert client.post("/_csrf/write", data={"csrf_token": value},
                       headers={"X-CSRF-Token": "wrong"}).status_code == 400


def test_token_cannot_be_reused_in_another_session(protected):
    first, second = protected.test_client(), protected.test_client()
    first_token, second_token = token(first), token(second)
    assert first_token != second_token
    assert second.post("/_csrf/write", headers={"X-CSRF-Token": first_token}).status_code == 400
    assert second.post("/_csrf/write", headers={"X-CSRF-Token": second_token}).status_code == 200


def test_forged_form_without_session_is_refused(protected):
    response = protected.test_client().post("/_csrf/write", data={"csrf_token": "attacker"})
    assert response.status_code == 400
    assert protected.csrf_writes == []


def test_get_and_head_do_not_require_token(protected):
    client = protected.test_client()
    for method in ("GET", "HEAD"):
        assert client.open("/_csrf/write", method=method).status_code == 200
    assert protected.csrf_writes == []


def test_token_is_stable_across_pages_and_not_cacheable(protected):
    client = protected.test_client()
    first = token(client)
    assert token(client, "/accounts/register") == first
    assert "no-store" in client.get("/accounts/login").headers["Cache-Control"]


def test_testing_defaults_off_and_production_defaults_on(app, monkeypatch):
    with app.test_request_context():
        assert csrf_protection_enabled() is False
        monkeypatch.setitem(app.config, "TESTING", False)
        assert csrf_protection_enabled() is True
        monkeypatch.setitem(app.config, "CSRF_ENABLED", True)
        monkeypatch.setitem(app.config, "TESTING", True)
        assert csrf_protection_enabled() is True


def test_token_helper_creates_a_random_session_value(protected):
    with protected.test_request_context():
        from flask import session
        value = csrf_token()
        assert value == session[CSRF_SESSION_KEY] == csrf_token()
        assert len(value) >= 32


def test_registration_requires_token_and_works_before_login(protected):
    client = protected.test_client()
    payload = {"name": "First Time", "email": "csrf-register@example.test",
               "mobile": "9300000090", "password": "fictional-password-1"}
    assert client.post("/accounts/register", json=payload).status_code == 400
    assert db.session.execute(db.select(User)).scalars().all() == []
    value = token(client, "/accounts/register")
    assert client.post("/accounts/register", json=payload,
                       headers={"X-CSRF-Token": value}).status_code == 201


@pytest.fixture
def world(protected):
    password = "fictional-password-1"
    hashed = hash_password(password)
    admin = User(name="CSRF Admin", email="csrf-admin@example.test", mobile="9300000091",
                 password_hash=hashed, role="administrator")
    candidate = User(name="CSRF Candidate", email="csrf-candidate@example.test", mobile="9300000092",
                     password_hash=hashed, role="candidate")
    db.session.add_all([admin, candidate])
    db.session.commit()
    application = Application(candidate_id=candidate.id, status="Submitted",
                              reference_number="ADM-CSRF-TEST")
    db.session.add(application)
    db.session.commit()
    for n, (kind, status) in enumerate([("Marksheet", "Pending"), ("ID Proof", "Rejected")]):
        db.session.add(Document(candidate_id=candidate.id, application_id=application.id,
                                document_type=kind, status=status, stored_name=f"csrf-{n}.pdf",
                                rejection_reason="Clearer copy needed" if status == "Rejected" else None))
    seed()
    db.session.commit()

    def login(user):
        client = protected.test_client()
        value = token(client)
        assert client.post("/accounts/login", json={"identifier": user.email, "password": password},
                           headers={"X-CSRF-Token": value}).status_code == 200
        return client

    return login(admin), login(candidate)


def test_login_and_logout_require_valid_token(protected, world):
    admin, _ = world
    assert admin.post("/accounts/logout").status_code == 400
    assert admin.get("/accounts/me").status_code == 200
    value = token(admin)
    assert admin.post("/accounts/logout", headers={"X-CSRF-Token": value}).status_code == 204
    assert admin.get("/accounts/me").status_code == 401


def test_all_current_rendered_post_forms_have_exactly_one_matching_token(world):
    admin, candidate = world
    college = db.session.execute(db.select(College)).scalars().first()
    branch = db.session.execute(db.select(Branch)).scalars().first()
    pages = [(candidate, path) for path in (
        "/", "/accounts/login", "/accounts/register", "/accounts/profile-page",
        "/application", "/documents/upload", "/documents", "/choices",
    )] + [(admin, path) for path in (
        "/admin/documents", "/admin/colleges/new", f"/admin/colleges/{college.id}/edit",
        f"/admin/colleges/{college.id}/branches/new", f"/admin/branches/{branch.id}/edit",
        f"/admin/branches/{branch.id}/seats", "/admin/allotment",
    )]
    count = 0
    for client, path in pages:
        response = client.get(path)
        assert response.status_code == 200, path
        parsed = Forms(response.get_data(as_text=True))
        assert parsed.token, path
        for form in parsed.forms:
            if form["method"] == "post":
                count += 1
                assert form["tokens"] == [parsed.token], (path, form)
    assert count >= 10


def test_document_review_uses_same_token_as_meta_and_accepts_header(world):
    admin, _ = world
    value = token(admin, "/admin/documents")
    document = db.session.execute(db.select(Document).filter_by(status="Pending")).scalar_one()
    url = f"/admin/documents/{document.id}/review"
    assert admin.post(url, json={"decision": "Approved"}).status_code == 400
    db.session.refresh(document)
    assert document.status == "Pending"
    response = admin.post(url, json={"decision": "Approved"}, headers={"X-CSRF-Token": value})
    assert response.status_code == 200
    db.session.refresh(document)
    assert document.status == "Approved"


def test_valid_csrf_does_not_bypass_role_checks(world):
    _, candidate = world
    value = token(candidate, "/documents")
    assert candidate.post("/api/v1/admin/allotment/runs/999/publish",
                          headers={"X-CSRF-Token": value}).status_code == 403


def test_document_upload_reject_resubmit_flow_with_central_csrf(protected, world, tmp_path):
    from io import BytesIO
    from pypdf import PdfWriter

    protected.config["DOCUMENT_UPLOAD_DIR"] = str(tmp_path / "uploads")
    admin, candidate = world

    def pdf():
        stream = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(stream)
        stream.seek(0)
        return stream, "fictional.pdf"

    value = token(candidate, "/documents/upload")
    assert candidate.post("/documents/upload", data={
        "csrf_token": value, "document_type": "Category Certificate", "file": pdf(),
    }).status_code == 302
    document = db.session.execute(db.select(Document).filter_by(
        document_type="Category Certificate")).scalar_one()
    admin_token = token(admin, "/admin/documents")
    assert admin.post(f"/admin/documents/{document.id}/review", json={
        "decision": "Rejected", "reason": "Clearer scan required",
    }, headers={"X-CSRF-Token": admin_token}).status_code == 200
    value = token(candidate, "/documents")
    assert candidate.post(f"/documents/{document.id}/resubmit", data={
        "csrf_token": value, "file": pdf(),
    }).status_code == 303
    db.session.refresh(document)
    assert document.status == "Pending"
    assert document.rejection_reason is None
    with candidate.session_transaction() as session:
        assert session["document_upload_token"] == session["document_resubmission_token"] == value


def test_profile_json_update_is_protected_and_still_works(world):
    _, candidate = world
    value = token(candidate, "/accounts/profile-page")
    payload = {"name": "Updated Fictional Candidate", "mobile": "9300000092"}
    assert candidate.put("/accounts/profile", json=payload).status_code == 400
    assert candidate.put("/accounts/profile", json=payload,
                         headers={"X-CSRF-Token": value}).status_code == 200
    assert candidate.get("/accounts/profile").json["name"] == payload["name"]


def test_catalogue_native_form_is_protected_and_still_works(world):
    admin, _ = world
    value = token(admin, "/admin/colleges/new")
    assert admin.post("/admin/colleges/new", data={"name": "New CSRF College"}).status_code == 400
    assert admin.post("/admin/colleges/new", data={
        "name": "New CSRF College", "csrf_token": value,
    }).status_code == 302
    assert db.session.execute(db.select(College).filter_by(name="New CSRF College")).scalar_one()
