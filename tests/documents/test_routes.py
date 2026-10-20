from io import BytesIO

import pytest

from pypdf import PdfWriter
from app.extensions import db
from app.documents.models import Document

def pdf_stream():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    output.seek(0)
    return output

@pytest.fixture
def demo_client(app, client, tmp_path, monkeypatch, login_as):
    monkeypatch.setitem(
        app.config,
        "DOCUMENT_UPLOAD_DIR",
        str(tmp_path / "uploads"),
    )
    return login_as(client)


def form_token(client):
    response = client.get("/documents/upload")
    assert response.status_code == 200

    with client.session_transaction() as session:
        return session["document_upload_token"]


def test_anonymous_redirects_to_login(client):
    response = client.get("/documents/upload")

    assert response.status_code == 302


def test_development_flag_cannot_bypass_login(app, client, monkeypatch):
    monkeypatch.setattr(app, "debug", False)
    monkeypatch.setitem(app.config, "DOCUMENT_DEV_FIXTURE", True)

    assert client.get("/documents/upload").status_code == 302


def test_upload_page_loads(demo_client):
    response = demo_client.get("/documents/upload")

    assert response.status_code == 200
    assert b"Upload admission document" in response.data


def test_valid_upload_saves_document(app, demo_client):
    token = form_token(demo_client)

    response = demo_client.post(
        "/documents/upload",
        data={
            "csrf_token": token,
            "document_type": "marksheet",
            "file": (pdf_stream(), "sample.pdf"),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Document uploaded successfully" in response.data

    document = db.session.execute(
        db.select(Document)
    ).scalar_one()

    assert document.candidate_id == 1
    assert document.application_id == 1
    assert document.status == "Pending"


def test_invalid_file_is_rejected(app, demo_client):
    token = form_token(demo_client)

    response = demo_client.post(
        "/documents/upload",
        data={
            "csrf_token": token,
            "document_type": "marksheet",
            "file": (pdf_stream(), "sample.exe"),
        },
    )

    assert response.status_code == 400
    assert b"Only PDF, JPEG and PNG" in response.data
    assert db.session.execute(
        db.select(db.func.count(Document.id))
    ).scalar_one() == 0


def test_missing_form_token_is_rejected(demo_client):
    response = demo_client.post(
        "/documents/upload",
        data={
            "document_type": "marksheet",
            "file": (pdf_stream(), "sample.pdf"),
        },
    )

    assert response.status_code == 400


def test_authenticated_nonlocal_access_is_allowed(demo_client):
    response = demo_client.get(
        "/documents/upload",
        environ_overrides={"REMOTE_ADDR": "192.0.2.10"},
    )

    assert response.status_code == 200