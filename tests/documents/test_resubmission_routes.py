"""Candidate resubmission HTTP authorization and validation."""
from io import BytesIO

import pytest
from pypdf import PdfWriter
from app.documents.models import Document
from app.extensions import db


@pytest.fixture
def setup(app, client, tmp_path, login_as):
    login_as(client)
    app.config.update(DOCUMENT_UPLOAD_DIR=str(tmp_path))
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


def test_logout_blocks_resubmit(setup, app):
    client, document, token = setup
    assert client.post('/accounts/logout').status_code == 204
    assert client.post(f'/documents/{document.id}/resubmit', data=payload(token)).status_code == 302


def test_oversized_request(setup):
    client, document, token = setup
    data = {'csrf_token': token, 'file': (BytesIO(b'x' * (3 * 1024 * 1024)), 'large.pdf')}
    assert client.post(f'/documents/{document.id}/resubmit', data=data).status_code == 413
    assert document.status == 'Rejected'


def test_reject_resubmit_download_and_approve_workflow(setup, app, tmp_path, login_as):
    client, document, candidate_token = setup
    document.status = 'Pending'
    document.rejection_reason = None
    db.session.commit()
    document_id = document.id
    login_as(client, 3)
    assert client.get('/admin/documents').status_code == 200
    with client.session_transaction() as session:
        admin_token = session['document_review_token']
    review_url = f'/admin/documents/{document_id}/review'
    response = client.post(review_url, json={
        'csrf_token': admin_token, 'decision': 'Rejected', 'reason': 'Upload a clearer scan',
    })
    assert response.status_code == 200
    login_as(client, 1)
    page = client.get('/documents')
    assert b'Upload a clearer scan' in page.data
    assert b'Resubmit document' in page.data
    replacement = payload(candidate_token)
    replacement_bytes = replacement['file'][0].getvalue()
    assert client.post(f'/documents/{document_id}/resubmit', data=replacement).status_code == 303
    assert not (tmp_path / 'old.pdf').exists()
    assert client.get(f'/admin/documents/{document_id}/file').status_code == 403
    login_as(client, 3)
    queue = client.get('/admin/documents.json').get_json()['documents']
    assert any(item['id'] == document_id and item['status'] == 'Pending' for item in queue)
    downloaded = client.get(f'/admin/documents/{document_id}/file')
    assert downloaded.status_code == 200
    assert downloaded.data == replacement_bytes
    downloaded.close()
    assert client.post(review_url, json={
        'csrf_token': admin_token, 'decision': 'Approved',
    }).status_code == 200
    login_as(client, 1)
    page = client.get('/documents')
    assert b'Approved' in page.data
    assert b'Resubmit document' not in page.data
    assert b'Upload a clearer scan' not in page.data
    assert client.post(f'/documents/{document_id}/resubmit', data=payload(candidate_token)).status_code == 409
