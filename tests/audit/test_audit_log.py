
"""Audit log: written by admin actions, readable by administrators, append-only."""

import pytest
from sqlalchemy.exc import DatabaseError
from flask import g
from types import SimpleNamespace

from app.audit.services import record_admin_action, record_audit
from app.audit.models import AuditLog
from app.extensions import db
from tests.catalogue.helpers import get_branch, get_college, login_client


MERIDIAN = "Meridian Institute of Technology"
CSE = "Computer Science and Engineering"


@pytest.fixture
def admin(app):
    return login_client(app, "administrator", 1)


def _entries():
    db.session.expire_all()
    return db.session.execute(
        db.select(AuditLog).order_by(AuditLog.id)
    ).scalars().all()


def test_catalogue_actions_write_audit_entries(seeded, admin):
    admin.post(
        "/admin/colleges/new",
        data={"name": "Audit College", "city": "Testville"},
    )
    college = get_college("Audit College")
    admin.post(
        f"/admin/colleges/{college.id}/edit",
        data={"name": "Audit College 2", "city": "X"},
    )
    admin.post(
        f"/admin/colleges/{college.id}/branches/new",
        data={"name": "Civil"},
    )
    branch = get_branch("Audit College 2", "Civil")
    admin.post(
        f"/admin/branches/{branch.id}/edit",
        data={"name": "Civil Engineering"},
    )
    admin.post(
        f"/admin/branches/{branch.id}/seats",
        data={"General": "10"},
    )

    entries = _entries()

    assert [e.action_type for e in entries] == [
        "college.create",
        "college.update",
        "branch.create",
        "branch.update",
        "seats.update",
    ]
    assert all(
        e.actor_id == admin.user_id and e.actor_role == "administrator"
        for e in entries
    )
    assert entries[0].target_type == "college"
    assert entries[0].target_id == college.id
    assert entries[4].target_type == "branch"
    assert entries[4].target_id == branch.id
    assert all(
        e.created_at is not None and e.outcome == "Success"
        for e in entries
    )


def test_rejected_actions_are_not_logged(seeded, admin):
    admin.post("/admin/colleges/new", data={"name": MERIDIAN})
    admin.post("/admin/colleges/new", data={"name": "  "})
    assert _entries() == []


def test_audit_page_and_json_for_administrator(seeded, admin):
    admin.post("/admin/colleges/new", data={"name": "Audit College"})

    page = admin.get("/admin/audit-logs")
    assert page.status_code == 200
    assert b"college.create" in page.data

    body = admin.get("/admin/audit-logs.json").get_json()
    assert body[0]["actionType"] == "college.create"
    assert body[0]["actor"] == admin.user_id
    assert body[0]["timestamp"]
    assert body[0]["target"]["type"] == "college"


def test_audit_filter_by_action_type(seeded, admin):
    admin.post("/admin/colleges/new", data={"name": "Audit College"})
    college = get_college("Audit College")
    admin.post(
        f"/admin/colleges/{college.id}/branches/new",
        data={"name": "Civil"},
    )

    body = admin.get(
        "/admin/audit-logs.json?action_type=branch.create"
    ).get_json()

    assert [e["actionType"] for e in body] == ["branch.create"]


def test_audit_log_needs_the_administrator_role(app):
    assert app.test_client().get("/admin/audit-logs").status_code == 401
    assert app.test_client().get("/admin/audit-logs.json").status_code == 401

    candidate = login_client(app, "candidate", 2)
    assert candidate.get("/admin/audit-logs").status_code == 403


def test_there_is_no_way_to_change_the_log_over_http(app, admin):
    for method in ("post", "put", "patch", "delete"):
        assert getattr(admin, method)("/admin/audit-logs").status_code == 405


def test_database_rejects_update_and_delete(app):
    entry = record_audit(1, "test.action", "college", 5)
    entry_id = entry.id

    with pytest.raises(DatabaseError):
        db.session.execute(
            db.text(
                "UPDATE audit_log SET action_type = 'x' WHERE id = :i"
            ),
            {"i": entry_id},
        )

    db.session.rollback()

    with pytest.raises(DatabaseError):
        db.session.execute(
            db.text("DELETE FROM audit_log WHERE id = :i"),
            {"i": entry_id},
        )

    db.session.rollback()

    assert len(_entries()) == 1
    assert _entries()[0].action_type == "test.action"


def test_orm_update_is_also_rejected(app):
    entry = record_audit(1, "test.action")
    entry.action_type = "tampered"

    with pytest.raises(DatabaseError):
        db.session.commit()

    db.session.rollback()

    assert _entries()[0].action_type == "test.action"


def test_record_audit_commit_false_does_not_commit(app):
    entry = record_audit(
        1,
        "test.uncommitted",
        commit=False,
    )

    assert entry in db.session
    assert entry.id is None

    # Roll back the current transaction.
    db.session.rollback()

    # The entry must not have been persisted.
    assert db.session.execute(
        db.select(AuditLog).where(
            AuditLog.action_type == "test.uncommitted"
        )
    ).scalar_one_or_none() is None


def test_record_audit_commit_true_persists_entry(app):
    entry = record_audit(
        1,
        "test.committed",
        commit=True,
    )

    entry_id = entry.id
    db.session.rollback()

    persisted = db.session.get(AuditLog, entry_id)

    assert persisted is not None
    assert persisted.action_type == "test.committed"


def test_record_admin_action_commit_false(app):
    with app.test_request_context():
        g.current_user = SimpleNamespace(
            id=1,
            role="administrator",
        )

        entry = record_admin_action(
            "test.admin.uncommitted",
            commit=False,
        )

        assert entry.actor_id == 1
        assert entry.actor_role == "administrator"
        assert entry in db.session
        assert entry.id is None

        db.session.rollback()

    assert db.session.execute(
        db.select(AuditLog).where(
            AuditLog.action_type == "test.admin.uncommitted"
        )
    ).scalar_one_or_none() is None


def test_record_admin_action_commit_true(app):
    with app.test_request_context():
        g.current_user = SimpleNamespace(
            id=1,
            role="administrator",
        )

        entry = record_admin_action(
            "test.admin.committed",
            commit=True,
        )

        entry_id = entry.id
        db.session.rollback()

    persisted = db.session.get(AuditLog, entry_id)

    assert persisted is not None
    assert persisted.action_type == "test.admin.committed"
