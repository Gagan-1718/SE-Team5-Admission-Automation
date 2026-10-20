"""Candidate resubmission HTTP authorization and validation."""
from io import BytesIO

import pytest
from pypdf import PdfWriter
from app.documents.models import Document
from app.extensions import db


@pytest.fixture
def setup(app, client, tmp_path):
    app.config.update(DEBUG=True, DOCUMENT_DEV_FIXTURE=True,
                      DOCUMENT_UPLOAD_DIR=str(tmp_path))
    document = Document(candidate_id=1, application_id=1, document_type="Marksheet",
                        stored_name="old.pdf", status="Rejected", rejection_reason="Unreadable")
    db.session.add(document)
    db.session.commit()
    (tmp_path / "old.pdf").write_bytes(b"original")
    client.get('/documents')
    with client.session_transaction() as session:
        token = session['document_resubmission_token']
    return client, document, token


def payload(token):
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(stream)
    stream.seek(0)
    return {'csrf_token': token, 'file': (stream, 'clear.pdf')}


def test_success_redirect_and_pending_page(setup):
    client, document, token = setup
    response = client.post(f'/documents/{document.id}/resubmit', data=payload(token))
    assert response.status_code == 303
    page = client.get(response.location)
    assert b'Replacement submitted' in page.data
    assert b'Pending Verification' in page.data
    assert b'Resubmit document' not in page.data
    assert b'Unreadable' not in page.data


@pytest.mark.parametrize('token', ['', 'invalid'])
def test_bad_token_cannot_change_document(setup, token):
    client, document, _ = setup
    response = client.post(f'/documents/{document.id}/resubmit', data=payload(token))
    assert response.status_code == 400
    assert document.status == 'Rejected'


def test_other_owner_hidden(setup):
    client, document, token = setup
    document.candidate_id = 2
    db.session.commit()
    assert client.post(f'/documents/{document.id}/resubmit', data=payload(token)).status_code == 404
    assert document.status == 'Rejected'


@pytest.mark.parametrize('status', ['Pending', 'Approved'])
def test_wrong_status_conflict(setup, status):
    client, document, token = setup
    document.status = status
    db.session.commit()
    assert client.post(f'/documents/{document.id}/resubmit', data=payload(token)).status_code == 409


def test_missing_file_validation(setup):
    client, document, token = setup
    assert client.post(f'/documents/{document.id}/resubmit', data={'csrf_token': token}).status_code == 422
    assert document.status == 'Rejected'


def test_disabled_identity_blocks_resubmit(setup, app):
    client, document, token = setup
    app.config['DOCUMENT_DEV_FIXTURE'] = False
    assert client.post(f'/documents/{document.id}/resubmit', data=payload(token)).status_code == 503


def test_oversized_request(setup):
    client, document, token = setup
    data = {'csrf_token': token, 'file': (BytesIO(b'x' * (3 * 1024 * 1024)), 'large.pdf')}
    assert client.post(f'/documents/{document.id}/resubmit', data=data).status_code == 413
    assert document.status == 'Rejected'
