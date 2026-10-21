"""The Sprint One demonstration as one automated test (docs/DEVIATIONS.md, README 'Demo walkthrough').

register -> login -> exam details -> draft -> submit -> upload -> admin review -> resubmit ->
approve -> eligibility -> catalogue. Fictional data only; real seeds, real logins, real routes.

Things that are not connected yet are written as `xfail` tests with the reason. They do not
fail the build; when a teammate connects the piece, the test starts passing (XPASS) and the
`xfail` mark should be deleted. Together they are the list of what is left for the demo.
"""
import re
from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfWriter

from app.documents.models import Document
from app.extensions import db

ADMIN_PASSWORD = "demo-admin-password-1"
CANDIDATE_PASSWORD = "fictional-pass-1"
CANDIDATE = {"name": "Fictional Candidate", "email": "demo.candidate@example.test",
             "mobile": "9123456780", "password": CANDIDATE_PASSWORD}
COMPLETE_APPLICATION = {"guardian_name": "Fictional Guardian", "guardian_mobile": "9876543210",
                        "school_name": "Fictional PU College", "board": "CBSE", "percentage": "88.5"}
ELIGIBILITY_STATUSES = {"Pending", "Eligible", "Not Eligible"}
REQUIRED_TYPES = {"Marksheet", "ID Proof", "Category Certificate"}  # proposed in the Day 2 guide


# ----------------------------------------------------------------------------- helpers

def pdf_file(name="marksheet.pdf"):
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(stream)
    stream.seek(0)
    return stream, name


def image_file(name, fmt):
    stream = BytesIO()
    Image.new("RGB", (40, 40), "white").save(stream, fmt)
    stream.seek(0)
    return stream, name


def session_value(client, page, key):
    assert client.get(page).status_code == 200
    with client.session_transaction() as session:
        return session[key]


def login(client, identifier, password):
    response = client.post("/accounts/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200
    return client


@pytest.fixture
def seeded(app, monkeypatch, tmp_path):
    """The app with every module's fictional seed data, exactly as `flask seed-db` creates it."""
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", ADMIN_PASSWORD)
    app.config["DOCUMENT_UPLOAD_DIR"] = str(tmp_path / "uploads")
    result = app.test_cli_runner().invoke(args=["seed-db"])
    assert result.exit_code == 0, result.output
    return app


def new_candidate(app):
    """A registered, logged-in candidate with exam details (rank 1000, General) entered."""
    client = app.test_client()
    assert client.post("/accounts/register", json=CANDIDATE).status_code == 201
    login(client, CANDIDATE["email"], CANDIDATE_PASSWORD)
    exam = {"exam_type": "KCET", "rank": 1000, "category": "General", "score": 185.0}
    assert client.put("/accounts/exam-details", json=exam).status_code == 200
    return client


def submit_application(client):
    response = client.post("/application/submit", data=COMPLETE_APPLICATION)
    assert response.status_code == 302
    return re.search(rb"ADM-\d{4}-\d{6}", client.get("/application").data).group().decode()


def upload_all_documents(client):
    token = session_value(client, "/documents/upload", "document_upload_token")
    files = {"Marksheet": pdf_file(), "ID Proof": image_file("id.png", "PNG"),
             "Category Certificate": image_file("cert.jpg", "JPEG")}
    for document_type, file in files.items():
        response = client.post("/documents/upload", data={
            "csrf_token": token, "document_type": document_type, "file": file})
        assert response.status_code == 302, (document_type, response.status_code)


def review(admin, document_id, decision, reason=None):
    token = session_value(admin, "/admin/documents", "document_review_token")
    body = {"csrf_token": token, "decision": decision}
    if reason is not None:
        body["reason"] = reason
    return admin.post(f"/admin/documents/{document_id}/review", json=body)


def statuses_in_database(app, candidate_id):
    """{document_type: status} for one candidate, read directly from the documents table."""
    with app.app_context():
        rows = db.session.execute(db.select(Document).filter_by(candidate_id=candidate_id)).scalars().all()
        return {row.document_type: row.status for row in rows}


def pending_ids(admin):
    documents = admin.get("/admin/documents.json").get_json()["documents"]
    return {d["document_type"]: d["id"] for d in documents}


# ------------------------------------------------------------- the demonstration flow

def test_full_demo_flow(seeded):
    app = seeded
    candidate = app.test_client()

    # 1-2: registration and login rules (TC-001, TC-002)
    assert candidate.post("/accounts/register", json=CANDIDATE).status_code == 201
    assert candidate.post("/accounts/register", json={**CANDIDATE, "mobile": "9123456781"}).status_code == 409
    wrong = candidate.post("/accounts/login", json={"identifier": CANDIDATE["email"], "password": "wrong-password"})
    assert wrong.status_code == 401
    login(candidate, CANDIDATE["email"], CANDIDATE_PASSWORD)

    # 3: rank and category only from the seeded exam records (TC-003)
    made_up = {"exam_type": "KCET", "rank": 77777, "category": "General", "score": 1.0}
    assert candidate.put("/accounts/exam-details", json=made_up).status_code == 422
    seeded_row = {"exam_type": "KCET", "rank": 1000, "category": "General", "score": 185.0}
    assert candidate.put("/accounts/exam-details", json=seeded_row).status_code == 200

    # 4: save a partial draft, log out, log in, the draft is still there (TC-004)
    candidate.post("/application", data={"guardian_name": "Fictional Guardian", "board": "CBSE"})
    assert candidate.post("/accounts/logout").status_code == 204
    login(candidate, CANDIDATE["email"], CANDIDATE_PASSWORD)
    assert b"Fictional Guardian" in candidate.get("/application").data

    # 5: incomplete submit is refused, complete submit gives a unique reference (TC-005)
    assert candidate.post("/application/submit", data={"guardian_name": "Fictional Guardian"}).status_code == 422
    reference = submit_application(candidate)
    assert reference.startswith("ADM-")
    assert candidate.post("/application/submit", data=COMPLETE_APPLICATION).status_code == 409

    # 6: documents: valid files accepted, invalid refused (TC-006)
    token = session_value(candidate, "/documents/upload", "document_upload_token")
    bad = candidate.post("/documents/upload", data={"csrf_token": token, "document_type": "Marksheet",
                                                    "file": (BytesIO(b"plain text"), "notes.txt")})
    assert bad.status_code == 400
    upload_all_documents(candidate)
    assert statuses_in_database(app, 2) == {t: "Pending" for t in REQUIRED_TYPES}  # candidate is user 2

    # 7: the seeded administrator reviews: a reason is mandatory, then visible to the candidate (TC-007)
    admin = login(app.test_client(), "admin@example.test", ADMIN_PASSWORD)
    ids = pending_ids(admin)
    assert set(ids) == REQUIRED_TYPES
    assert review(admin, ids["Marksheet"], "Rejected").status_code == 422
    assert review(admin, ids["Marksheet"], "Rejected", "Image is not readable").status_code == 200
    assert b"Image is not readable" in candidate.get("/documents").data
    assert review(admin, ids["ID Proof"], "Approved").status_code == 200
    assert review(admin, ids["Category Certificate"], "Approved").status_code == 200
    assert statuses_in_database(app, 2) == {"Marksheet": "Rejected", "ID Proof": "Approved",
                                            "Category Certificate": "Approved"}

    # 8: resubmission goes back to Pending and can then be approved (TC-008)
    resubmit_token = session_value(candidate, "/documents", "document_resubmission_token")
    again = candidate.post(f"/documents/{ids['Marksheet']}/resubmit",
                           data={"csrf_token": resubmit_token, "file": pdf_file("marksheet_corrected.pdf")})
    assert again.status_code == 303
    assert review(admin, ids["Marksheet"], "Approved").status_code == 200
    assert set(statuses_in_database(app, 2).values()) == {"Approved"}

    # 9: eligibility returns a valid status and a reason (TC-009; inputs are still temporary, see xfails)
    eligibility = candidate.get("/api/v1/candidates/me/eligibility").get_json()
    assert eligibility["status"] in ELIGIBILITY_STATUSES and eligibility["reason"]

    # 10: the candidate can browse the seeded catalogue (TC-010)
    colleges = candidate.get("/colleges")
    assert colleges.status_code == 200
    assert b"Meridian Institute of Technology" in colleges.data

    # 12: access control (TC-021, TC-022)
    assert candidate.get("/admin/documents").status_code == 403
    assert app.test_client().get("/application").status_code == 302
    assert app.test_client().get("/admin/documents").status_code in (302, 401, 403)


# ----------------------------------------------- not connected yet: the list of what is left

@pytest.mark.xfail(reason="Catalogue admin guard is not connected to the login yet (Tasya): "
                          "the administrator gets 403 on /admin/colleges. Use role_required('administrator').")
def test_administrator_can_open_the_catalogue_admin_page(seeded):
    admin = login(seeded.test_client(), "admin@example.test", ADMIN_PASSWORD)
    assert admin.get("/admin/colleges").status_code == 200


@pytest.mark.xfail(reason="Eligibility still uses temporary inputs (Tasya): it always says Eligible. "
                          "It must say Pending until all required documents are approved.")
def test_eligibility_is_pending_until_the_documents_are_approved(seeded):
    candidate = new_candidate(seeded)
    submit_application(candidate)
    status = candidate.get("/api/v1/candidates/me/eligibility").get_json()["status"]
    assert status == "Pending"


@pytest.mark.xfail(reason="Eligibility must use the candidate's real rank and category (Tasya): "
                          "rank 90000 General is above the cut-off and must be Not Eligible.")
def test_eligibility_uses_the_real_exam_details(seeded):
    client = seeded.test_client()
    client.post("/accounts/register", json=CANDIDATE)
    login(client, CANDIDATE["email"], CANDIDATE_PASSWORD)
    exam = {"exam_type": "KCET", "rank": 90000, "category": "General", "score": 60.0}
    assert client.put("/accounts/exam-details", json=exam).status_code == 200
    result = client.get("/api/v1/candidates/me/eligibility").get_json()
    assert result["status"] in {"Pending", "Not Eligible"}


@pytest.mark.xfail(reason="Eligibility pages are not login-protected yet (Tasya): anonymous visitors get 200.")
def test_anonymous_cannot_see_eligibility(seeded):
    anonymous = seeded.test_client()
    assert anonymous.get("/api/v1/candidates/me/eligibility").status_code == 401
    assert anonymous.get("/eligibility").status_code == 302


@pytest.mark.xfail(reason="Admin dashboard is not built yet (Tasya, #27): /admin/dashboard returns 404.")
def test_administrator_dashboard_exists(seeded):
    admin = login(seeded.test_client(), "admin@example.test", ADMIN_PASSWORD)
    assert admin.get("/admin/dashboard").status_code == 200


@pytest.mark.xfail(reason="Audit log is not built yet (Tasya, #28): /admin/audit-logs returns 404.")
def test_administrator_can_read_the_audit_log(seeded):
    admin = login(seeded.test_client(), "admin@example.test", ADMIN_PASSWORD)
    assert admin.get("/admin/audit-logs").status_code == 200


@pytest.mark.xfail(reason="Documents are not linked to users and applications in the database yet (Dikshith): "
                          "documents.candidate_id must be a foreign key to users.id.")
def test_documents_candidate_id_is_a_foreign_key(seeded):
    from sqlalchemy import inspect
    foreign_keys = inspect(db.engine).get_foreign_keys("documents")
    assert any(fk["referred_table"] == "users" for fk in foreign_keys)


@pytest.mark.xfail(reason="all_documents_approved(candidate_id) and REQUIRED_DOCUMENT_TYPES are not in "
                          "app/documents/services.py yet (Dikshith). Eligibility (Tasya) needs them.")
def test_documents_module_exposes_the_agreed_interface(seeded):
    from app.documents import services
    assert set(services.REQUIRED_DOCUMENT_TYPES) == REQUIRED_TYPES
    with seeded.app_context():
        assert services.all_documents_approved(999) is False


@pytest.mark.xfail(reason="The upload accepts any document type text (Dikshith); it should accept only "
                          "Marksheet, ID Proof and Category Certificate.")
def test_upload_refuses_an_unknown_document_type(seeded):
    candidate = new_candidate(seeded)
    submit_application(candidate)
    token = session_value(candidate, "/documents/upload", "document_upload_token")
    response = candidate.post("/documents/upload", data={
        "csrf_token": token, "document_type": "Holiday Photo", "file": pdf_file()})
    assert response.status_code == 400


@pytest.mark.xfail(reason="The profile page has no exam-details form yet (Varun): candidates can only enter "
                          "exam details through PUT /accounts/exam-details, not in the browser (demo step 3).")
def test_profile_page_has_an_exam_details_form(seeded):
    client = seeded.test_client()
    client.post("/accounts/register", json=CANDIDATE)
    login(client, CANDIDATE["email"], CANDIDATE_PASSWORD)
    page = client.get("/accounts/profile-page")
    assert page.status_code == 200
    assert b"exam_type" in page.data
