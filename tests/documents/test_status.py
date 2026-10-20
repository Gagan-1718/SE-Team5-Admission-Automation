"""Candidate document status and ADM-F-007 rejection reason visibility."""

import pytest

from app.documents.models import Document
from app.extensions import db


@pytest.fixture
def candidate_client(app, client, login_as):
    return login_as(client)


def add_document(candidate_id=1, status="Pending", reason=None, name="sample.pdf"):
    document = Document(
        candidate_id=candidate_id, application_id=candidate_id,
        document_type="Marksheet", stored_name=name,
        status=status, rejection_reason=reason,
    )
    db.session.add(document)
    db.session.commit()
    return document


def test_empty_status_page(candidate_client):
    response = candidate_client.get('/documents')
    assert response.status_code == 200
    assert b'No documents uploaded.' in response.data
    assert response.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('status,label', [
    ('Pending', b'Pending Verification'), ('Approved', b'Approved'), ('Rejected', b'Rejected')
])
def test_status_display(candidate_client, status, label):
    add_document(status=status)
    response = candidate_client.get('/documents')
    assert response.status_code == 200
    assert label in response.data


def test_hides_other_candidate_even_with_query_parameter(candidate_client):
    add_document(reason='My rejection reason', status='Rejected')
    add_document(2, 'Rejected', 'Private other candidate reason', 'other.pdf')
    response = candidate_client.get('/documents?candidate_id=2')
    assert b'My rejection reason' in response.data
    assert b'Private other candidate reason' not in response.data
    assert b'other.pdf' not in response.data


def test_admin_rejection_becomes_visible_to_candidate(app, candidate_client, login_as):
    document = add_document()
    login_as(candidate_client, 3)
    assert candidate_client.get('/admin/documents').status_code == 200
    with candidate_client.session_transaction() as session:
        token = session['document_review_token']
    result = candidate_client.post(f'/admin/documents/{document.id}/review', json={
        'decision': 'Rejected', 'reason': 'Upload a clearer scan', 'csrf_token': token,
    })
    assert result.status_code == 200
    login_as(candidate_client, 1)
    response = candidate_client.get('/documents')
    assert b'Rejected' in response.data
    assert b'Upload a clearer scan' in response.data
    assert candidate_client.get('/admin/documents').status_code == 403


def test_reason_is_html_escaped(candidate_client):
    add_document(status='Rejected', reason='<script>alert(1)</script>')
    response = candidate_client.get('/documents')
    assert b'<script>alert(1)</script>' not in response.data
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in response.data


def test_anonymous_status_redirects(client):
    assert client.get('/documents').status_code == 302


def test_debug_flag_does_not_bypass_login(app, client):
    app.config.update(DEBUG=False, DOCUMENT_DEV_FIXTURE=True)
    assert client.get('/documents').status_code == 302


def test_authenticated_nonlocal_status_works(candidate_client):
    assert candidate_client.get('/documents', environ_overrides={
        'REMOTE_ADDR': '192.0.2.10',
    }).status_code == 200
