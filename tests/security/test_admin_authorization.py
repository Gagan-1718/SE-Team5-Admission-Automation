"""TC-022: exercise every implemented admin page/API with real Accounts sessions."""
import re

import pytest

from app.application.models import Application
from app.audit.models import AuditLog
from app.catalogue.models import Branch, College, Seat
from app.catalogue.seed import seed
from app.documents.models import Document
from app.extensions import db
from tests.catalogue.helpers import login_client
from app.eligibility.models import EligibilityRule
from app.eligibility.seed import seed as seed_eligibility

@pytest.fixture
def admin_resources(app, tmp_path):
    seed()
    seed_eligibility()
    admin = login_client(app, "administrator", 1)
    candidate = login_client(app, "candidate", 2)
    application = Application(candidate_id=candidate.user_id, status="Submitted",
                              reference_number="ADM-SECURITY-TEST")
    db.session.add(application)
    db.session.commit()
    document = Document(candidate_id=candidate.user_id, application_id=application.id,
                        document_type="Marksheet", stored_name="security-test.pdf", status="Pending")
    db.session.add(document)
    db.session.commit()
    directory = tmp_path / "uploads"
    directory.mkdir()
    (directory / document.stored_name).write_bytes(b"%PDF-fictional-test-file")
    app.config["DOCUMENT_UPLOAD_DIR"] = str(directory)
    ids = {
        "college_id": db.session.execute(db.select(College.id)).scalars().first(),
        "branch_id": db.session.execute(db.select(Branch.id)).scalars().first(),
        "document_id": document.id,
        "rule_id": db.session.execute(
            db.select(EligibilityRule.id)
        ).scalars().first(),
    }
    return admin, candidate, ids


def admin_requests(app, ids):
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/admin/"):
            path = re.sub(r"<(?:[^:>]+:)?([^>]+)>", lambda m: str(ids[m.group(1)]), rule.rule)
            for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
                yield method, path


def data_snapshot():
    return {
        model.__tablename__: [
            tuple(getattr(row, column.name) for column in model.__table__.columns)
            for row in db.session.execute(db.select(model).order_by(model.id)).scalars()
        ]
        for model in (College, Branch, Seat, Document, Application, AuditLog)
    }


@pytest.mark.parametrize("role,expected", [(None, 401), ("candidate", 403)])
def test_every_admin_route_denies_unauthorized_users_without_mutation(app, admin_resources, role, expected):
    _, candidate, ids = admin_resources
    client = candidate if role else app.test_client()
    before = data_snapshot()
    requests = list(admin_requests(app, ids))
    assert requests
    for method, path in requests:
        response = client.open(path, method=method, json={"decision": "Approved", "General": 999})
        assert response.status_code == expected, (method, path, response.status_code)
    db.session.expire_all()
    assert data_snapshot() == before


def test_administrator_can_open_every_admin_get_route_and_logout_revokes_access(app, admin_resources):
    admin, _, ids = admin_resources
    paths = [path for method, path in admin_requests(app, ids) if method == "GET"]
    assert paths
    for path in paths:
        assert admin.get(path).status_code == 200, path
    assert admin.post("/accounts/logout").status_code == 204
    for path in paths:
        assert admin.get(path).status_code == 401, path
