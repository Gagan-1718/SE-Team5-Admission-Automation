"""Document tests use real Accounts sessions and submitted Applications."""
import pytest
from app.accounts.models import User
from app.accounts.security import hash_password
from app.application.models import Application
from app.extensions import db

PASSWORD = "fictional-password-1"

@pytest.fixture(scope="session")
def document_password_hash():
    return hash_password(PASSWORD)

@pytest.fixture(autouse=True)
def document_accounts(app, document_password_hash):
    for number, role in ((1, "candidate"), (2, "candidate"), (3, "administrator")):
        db.session.add(User(id=number, name=f"Test User {number}",
                            email=f"document{number}@example.test", mobile=f"900000000{number}",
                            password_hash=document_password_hash, role=role))
    db.session.commit()
    for number in (1, 2):
        db.session.add(Application(id=number, candidate_id=number, status="Submitted",
                                   reference_number=f"ADM-TEST-{number}"))
    db.session.commit()

@pytest.fixture
def login_as(document_accounts):
    def login(client, number=1):
        response = client.post('/accounts/login', json={
            'identifier': f'document{number}@example.test', 'password': PASSWORD})
        assert response.status_code == 200
        return client
    return login
