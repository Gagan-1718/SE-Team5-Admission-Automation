"""TC-017 and TC-022 publication API checks with real Accounts sessions."""
import pytest

from app.allotment.models import AllotmentRun
from app.audit.models import AuditLog
from app.extensions import db
from app.results.models import ResultPublication
from tests.catalogue.helpers import login_client


@pytest.fixture
def world(app):
    admin = login_client(app, "administrator", 101)
    candidate = login_client(app, "candidate", 102)
    run = AllotmentRun(run_by=admin.user_id)
    db.session.add(run)
    db.session.commit()
    return admin, candidate, run.id


def url(run_id):
    return f"/api/v1/admin/allotment/runs/{run_id}/publish"


def count(model):
    return db.session.execute(db.select(db.func.count(model.id))).scalar_one()


def test_admin_publication_uses_authenticated_actor(world):
    admin, candidate, run_id = world
    response = admin.post(url(run_id), json={"actor_id": candidate.user_id})
    assert response.status_code == 201
    assert response.json["run_id"] == run_id
    assert response.json["published_by"] == admin.user_id
    assert response.json["published_at"]
    publication = db.session.execute(db.select(ResultPublication)).scalar_one()
    entry = db.session.execute(db.select(AuditLog)).scalar_one()
    assert publication.published_by == entry.actor_id == admin.user_id
    assert entry.action_type == "results.publish"
    assert entry.target_id == run_id


@pytest.mark.parametrize("role,expected", [("anonymous", 401), ("candidate", 403)])
def test_unauthorized_publication_changes_nothing(app, world, role, expected):
    _, candidate, run_id = world
    client = candidate if role == "candidate" else app.test_client()
    assert client.post(url(run_id)).status_code == expected
    assert count(ResultPublication) == count(AuditLog) == 0


def test_unknown_run_returns_clear_404(world):
    admin, _, _ = world
    response = admin.post(url(99999))
    assert response.status_code == 404
    assert response.json["error"] == "RunNotFound"
    assert response.json["message"]
    assert count(ResultPublication) == count(AuditLog) == 0


def test_duplicate_publication_returns_409_with_one_audit(world):
    admin, _, run_id = world
    assert admin.post(url(run_id)).status_code == 201
    response = admin.post(url(run_id))
    assert response.status_code == 409
    assert response.json["error"] == "AlreadyPublished"
    assert count(ResultPublication) == count(AuditLog) == 1


def test_get_cannot_publish(world):
    admin, _, run_id = world
    assert admin.get(url(run_id)).status_code == 405
    assert count(ResultPublication) == count(AuditLog) == 0


def test_logout_revokes_publication_access(world):
    admin, _, run_id = world
    assert admin.post("/accounts/logout").status_code == 204
    assert admin.post(url(run_id)).status_code == 401
    assert count(ResultPublication) == count(AuditLog) == 0
