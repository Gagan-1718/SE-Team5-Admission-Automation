"""ADM-F-007 review state transitions, authorization and candidate visibility."""

import pytest

from app.extensions import db
from app.documents.models import Document
from app.documents.services import review_document


@pytest.fixture
def document(app, tmp_path):
    app.config['DOCUMENT_UPLOAD_DIR'] = str(tmp_path / 'uploads')
    directory = tmp_path / 'uploads'
    directory.mkdir()
    (directory / 'sample.pdf').write_bytes(b'%PDF-fictional-test-file')
    item = Document(candidate_id=1, application_id=1, document_type='Marksheet',
                    stored_name='sample.pdf', status='Pending')
    db.session.add(item)
    db.session.commit()
    return item


@pytest.fixture
def admin(app, client):
    app.config['DOCUMENTS_ADMIN_GUARD'] = lambda: True
    assert client.get('/admin/documents').status_code == 200
    with client.session_transaction() as session:
        token = session['document_review_token']
    return client, token


def decide(admin, document, decision, reason=None):
    client, token = admin
    return client.post(f'/admin/documents/{document.id}/review', json={
        'decision': decision, 'reason': reason, 'csrf_token': token})


@pytest.mark.parametrize('guard', [None, False, lambda: False, lambda: 'administrator'])
def test_admin_routes_deny_by_default(app, client, document, guard):
    app.config['DOCUMENTS_ADMIN_GUARD'] = guard
    assert client.get('/admin/documents').status_code == 403
    assert client.get('/admin/documents.json').status_code == 403
    assert client.get(f'/admin/documents/{document.id}/file').status_code == 403
    assert client.post(f'/admin/documents/{document.id}/review',
                       json={'decision': 'Approved'}).status_code == 403
    db.session.refresh(document)
    assert document.status == 'Pending'


def test_pending_queue_filters_records(admin, document):
    db.session.add(Document(candidate_id=2, application_id=2, document_type='ID Proof',
                            stored_name='other.pdf', status='Approved'))
    db.session.commit()
    response = admin[0].get('/admin/documents.json')
    assert [d['id'] for d in response.json['documents']] == [document.id]
    assert admin[0].get('/admin/documents?status=unknown').status_code == 400


def test_approve(admin, document):
    response = decide(admin, document, 'Approved')
    assert response.status_code == 200
    db.session.refresh(document)
    assert document.status == 'Approved'
    assert document.rejection_reason is None
    assert decide(admin, document, 'Rejected', 'Changed my mind').status_code == 409
    db.session.refresh(document)
    assert document.status == 'Approved'


@pytest.mark.parametrize('reason', [None, '', '   ', 123])
def test_rejection_requires_text_reason(admin, document, reason):
    assert decide(admin, document, 'Rejected', reason).status_code == 422
    db.session.refresh(document)
    assert document.status == 'Pending'
    assert document.rejection_reason is None


def test_reject_stores_reason(admin, document):
    response = decide(admin, document, 'Rejected', '  Please upload a clear copy  ')
    assert response.status_code == 200
    db.session.refresh(document)
    assert document.status == 'Rejected'
    assert document.rejection_reason == 'Please upload a clear copy'


@pytest.mark.parametrize('decision', ['Pending', 'invalid', None, ['Approved']])
def test_invalid_decision(admin, document, decision):
    assert decide(admin, document, decision).status_code == 422
    db.session.refresh(document)
    assert document.status == 'Pending'


def test_form_requires_token_and_redirects(admin, document):
    client, token = admin
    url = f'/admin/documents/{document.id}/review'
    assert client.post(url, data={'decision': 'Approved'}).status_code == 400
    assert client.post(url, data={'decision': 'Approved', 'csrf_token': token},
                       follow_redirects=True).status_code == 200
    db.session.refresh(document)
    assert document.status == 'Approved'


def test_missing_document(admin):
    client, token = admin
    assert client.post('/admin/documents/999/review', json={
        'decision': 'Approved', 'csrf_token': token}).status_code == 404
    assert client.get('/admin/documents/999/file').status_code == 404


def test_file_download(admin, document):
    response = admin[0].get(f'/admin/documents/{document.id}/file')
    assert response.status_code == 200
    assert response.data == b'%PDF-fictional-test-file'
    assert 'attachment' in response.headers['Content-Disposition']
    assert response.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('name', ['../outside.pdf', '..\\outside.pdf', 'missing.pdf'])
def test_unsafe_or_missing_stored_path(admin, document, name):
    document.stored_name = name
    db.session.commit()
    assert admin[0].get(f'/admin/documents/{document.id}/file').status_code == 404


def test_commit_failure_rolls_back_review(app, document, monkeypatch):
    def fail():
        raise RuntimeError('database unavailable')
    monkeypatch.setattr(db.session, 'commit', fail)
    with pytest.raises(RuntimeError, match='database unavailable'):
        review_document(document.id, 'Rejected', 'Unreadable')
    db.session.refresh(document)
    assert document.status == 'Pending'
    assert document.rejection_reason is None


def test_json_requires_session_token(admin, document):
    assert admin[0].post(f'/admin/documents/{document.id}/review',
                         json={'decision': 'Approved'}).status_code == 400
