"""Whole flow through real HTTP endpoints, without fixed candidate IDs."""
from io import BytesIO
from pypdf import PdfWriter
from app.accounts.models import ExamRecord, User
from app.accounts.security import hash_password
from app.documents.models import Document
from app.extensions import db

PASSWORD = "fictional-password-1"

def login(client, email):
    response = client.post('/accounts/login', json={'identifier': email, 'password': PASSWORD})
    assert response.status_code == 200

def token(client, page, key):
    assert client.get(page).status_code == 200
    with client.session_transaction() as session:
        return session[key]

def file_data():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(stream)
    stream.seek(0)
    return stream, 'marksheet.pdf'

def test_registered_candidate_submits_uploads_resubmits_and_gets_approval(app, tmp_path):
    app.config['DOCUMENT_UPLOAD_DIR'] = str(tmp_path / 'uploads')
    # Administrator is deliberately ID 1: the candidate must never inherit that ID.
    db.session.add(User(name='Admin', email='admin@example.test', mobile='9000000000',
                        role='administrator', password_hash=hash_password(PASSWORD)))
    db.session.commit()
    candidate = app.test_client()
    registered = candidate.post('/accounts/register', json={
        'name': 'Fictional Candidate', 'email': 'candidate@example.test',
        'mobile': '9000000001', 'date_of_birth': '2005-04-12', 'password': PASSWORD})
    assert registered.status_code == 201
    candidate_id = registered.json['user_id']
    assert candidate_id != 1
    login(candidate, 'candidate@example.test')
    db.session.add(ExamRecord(exam_type='KCET', rank=1000, category='General', score=185.0))
    db.session.commit()
    assert candidate.put('/accounts/exam-details', json={
        'exam_type': 'KCET', 'rank': 1000, 'category': 'General', 'score': 185.0}).status_code == 200
    assert candidate.get('/documents/upload').status_code == 409
    draft = candidate.post('/api/v1/applications', json={
        'guardian_name': 'Fictional Guardian', 'guardian_mobile': '9000000002',
        'school_name': 'Fictional School', 'board': 'CBSE', 'percentage': 85})
    assert draft.status_code == 201
    application_id = draft.json['applicationId']
    assert candidate.get('/documents/upload').status_code == 409
    assert candidate.post(f'/api/v1/applications/{application_id}/submit').status_code == 200
    assert b'Upload documents' in candidate.get('/application').data
    upload_token = token(candidate, '/documents/upload', 'document_upload_token')
    assert candidate.post('/documents/upload', data={
        'csrf_token': upload_token, 'document_type': 'Marksheet', 'file': file_data(),
        'candidate_id': '1', 'application_id': '999'}).status_code == 302
    document = db.session.execute(db.select(Document)).scalar_one()
    assert (document.candidate_id, document.application_id) == (candidate_id, application_id)
    document_id = document.id
    assert candidate.get('/admin/documents').status_code == 403
    admin = app.test_client()
    login(admin, 'admin@example.test')
    assert admin.get('/documents/upload').status_code == 403
    admin_token = token(admin, '/admin/documents', 'document_review_token')
    review_url = f'/admin/documents/{document_id}/review'
    assert admin.post(review_url, json={'csrf_token': admin_token, 'decision': 'Rejected',
                                       'reason': 'Clearer scan required'}).status_code == 200
    assert b'Clearer scan required' in candidate.get('/documents').data
    replacement_token = token(candidate, '/documents', 'document_resubmission_token')
    assert candidate.post(f'/documents/{document_id}/resubmit', data={
        'csrf_token': replacement_token, 'file': file_data()}).status_code == 303
    assert admin.post(review_url, json={'csrf_token': admin_token, 'decision': 'Approved'}).status_code == 200
    assert b'Approved' in candidate.get('/documents').data
    assert candidate.post('/accounts/logout').status_code == 204
    assert candidate.get('/documents').status_code == 302
    assert candidate.post(f'/documents/{document_id}/resubmit', data={
        'csrf_token': replacement_token, 'file': file_data()}).status_code == 302
