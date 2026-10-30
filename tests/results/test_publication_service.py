"""TC-017 service checks using real temporary database rows, not the allotment engine."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from app.accounts.models import User
from app.allotment.models import AllotmentRun
from app.audit.models import AuditLog
from app.extensions import db
from app.results import services
from app.results.models import ResultPublication


@pytest.fixture
def completed_run(app):
    admin = User(name="Publication Admin", email="publish@example.test",
                 mobile="9300000011", password_hash="fictional-test-hash", role="administrator")
    candidate = User(name="Candidate", email="publish-candidate@example.test",
                     mobile="9300000012", password_hash="fictional-test-hash", role="candidate")
    db.session.add_all([admin, candidate])
    db.session.commit()
    run = AllotmentRun(run_by=admin.id)
    db.session.add(run)
    db.session.commit()
    return run.id, admin.id, candidate.id


def rows(model):
    return db.session.execute(db.select(model)).scalars().all()


def test_publish_records_actor_time_and_audit_atomically(completed_run):
    run_id, actor_id, _ = completed_run
    assert services.is_published(run_id) is False
    publication = services.publish(run_id, actor_id)
    assert services.is_published(run_id) is True
    assert publication.run_id == run_id
    assert publication.published_by == actor_id
    assert publication.published_at is not None
    [entry] = rows(AuditLog)
    assert (entry.actor_id, entry.action_type, entry.target_type, entry.target_id) == (
        actor_id, "results.publish", "allotment_run", run_id)
    assert entry.outcome == "Success"


def test_repeat_publication_keeps_original_and_single_audit(completed_run):
    run_id, actor_id, _ = completed_run
    first = services.publish(run_id, actor_id)
    with pytest.raises(services.AlreadyPublished):
        services.publish(run_id, actor_id)
    assert rows(ResultPublication)[0].id == first.id
    assert len(rows(ResultPublication)) == len(rows(AuditLog)) == 1


def test_unknown_run_creates_nothing(completed_run):
    _, actor_id, _ = completed_run
    with pytest.raises(services.RunNotFound):
        services.publish(99999, actor_id)
    assert rows(ResultPublication) == rows(AuditLog) == []
    assert services.is_published(99999) is False


@pytest.mark.parametrize("actor", ["candidate", "missing"])
def test_service_denies_non_administrator(completed_run, actor):
    run_id, _, candidate_id = completed_run
    with pytest.raises(PermissionError):
        services.publish(run_id, candidate_id if actor == "candidate" else 99999)
    assert rows(ResultPublication) == rows(AuditLog) == []


def test_audit_failure_rolls_back_publication(completed_run, monkeypatch):
    run_id, actor_id, _ = completed_run

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(services, "record_audit", fail)
    with pytest.raises(RuntimeError, match="audit failure"):
        services.publish(run_id, actor_id)
    assert services.is_published(run_id) is False
    assert rows(ResultPublication) == rows(AuditLog) == []


def test_commit_failure_rolls_back_both_rows(completed_run, monkeypatch):
    run_id, actor_id, _ = completed_run

    def fail():
        raise RuntimeError("Simulated commit failure")

    monkeypatch.setattr(db.session, "commit", fail)
    with pytest.raises(RuntimeError, match="commit failure"):
        services.publish(run_id, actor_id)
    assert rows(ResultPublication) == rows(AuditLog) == []


def test_two_sessions_publish_once_with_one_audit(app, completed_run, monkeypatch):
    run_id, actor_id, _ = completed_run
    barrier = Barrier(2)
    original = services.is_published

    def check_together(value):
        exists = original(value)
        # Race both initial checks. The losing transaction's recovery check must
        # not wait again after the first transaction has committed.
        if not exists:
            barrier.wait(timeout=10)
        return exists

    monkeypatch.setattr(services, "is_published", check_together)
    db.session.remove()

    def worker():
        with app.app_context():
            try:
                return ("published", services.publish(run_id, actor_id).id)
            except services.AlreadyPublished:
                return ("conflict", None)
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        outcomes = [future.result(timeout=20)[0] for future in futures]
    assert sorted(outcomes) == ["conflict", "published"]
    assert len(rows(ResultPublication)) == len(rows(AuditLog)) == 1
