"""Cross-account and cross-application boundaries for document routes."""
from io import BytesIO
from pypdf import PdfWriter
from app.application.models import Application
from app.documents.models import Document
from app.extensions import db

def test_upload_uses_second_candidate_identity(app, client, login_as, tmp_path):
    app.config['DOCUMENT_UPLOAD_DIR'] = str(tmp_path)
    login_as(client, 2)
    assert client.get('/documents/upload').status_code == 200
    with client.session_transaction() as session:
        token = session['document_upload_token']
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(stream)
    stream.seek(0)
    assert client.post('/documents/upload', data={
        'csrf_token': token, 'document_type': 'Marksheet', 'file': (stream, 'sample.pdf'),
        'candidate_id': '1', 'application_id': '1'}).status_code == 302
    document = db.session.execute(db.select(Document)).scalar_one()
    assert (document.candidate_id, document.application_id) == (2, 2)

def test_draft_cannot_upload(app, client, login_as):
    application = db.session.get(Application, 1)
    application.status, application.reference_number = 'Draft', None
    db.session.commit()
    login_as(client)
    assert client.get('/documents/upload').status_code == 409
    assert client.post('/documents/upload').status_code == 409

def test_resubmission_rejects_mismatched_application(app, client, login_as):
    document = Document(candidate_id=1, application_id=2, document_type='Marksheet',
                        stored_name='legacy.pdf', status='Rejected')
    db.session.add(document)
    db.session.commit()
    login_as(client)
    assert client.post(f'/documents/{document.id}/resubmit').status_code == 404

def test_legacy_admin_guard_cannot_bypass_accounts(app, client):
    app.config['DOCUMENTS_ADMIN_GUARD'] = lambda: True
    assert client.get('/admin/documents').status_code == 401
    assert client.get('/admin/documents.json').status_code == 401
    assert client.get('/admin/documents/1/file').status_code == 401
    assert client.post('/admin/documents/1/review').status_code == 401
