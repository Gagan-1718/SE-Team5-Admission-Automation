"""Publication card states and real console form submissions (TC-017/TC-022)."""
import pytest
from flask import render_template

from app.allotment.models import AllotmentRun
from app.audit.models import AuditLog
from app.extensions import db
from app.results.models import ResultPublication
from app.results.services import publish, publication_details
from tests.catalogue.helpers import login_client


@pytest.fixture
def admin(app):
    return login_client(app, "administrator", 701)


@pytest.fixture
def run(admin):
    value = AllotmentRun(run_by=admin.user_id)
    db.session.add(value)
    db.session.commit()
    return value


def form_url(run):
    return f"/admin/allotment/runs/{run.id}/publish"


def publication_count():
    return db.session.execute(db.select(db.func.count(ResultPublication.id))).scalar_one()


def test_console_before_run_shows_disabled_publication(admin):
    page = admin.get("/admin/allotment").get_data(as_text=True)
    assert "Complete an allotment run before publishing results." in page
    assert '<button class="btn" type="button" disabled>Publish results</button>' in page
    assert "/publish" not in page


def test_completed_run_shows_publish_form_and_confirmation(admin, run):
    page = admin.get("/admin/allotment").get_data(as_text=True)
    assert page.count('id="publication-heading"') == 1
    assert f'action="{form_url(run)}"' in page
    assert "Run completed, not published" in page
    assert "return confirm(" in page
    assert "This can be done only once." in page
    assert '<button class="btn primary" type="submit">Publish results</button>' in page


def test_native_publish_redirects_back_to_html_console_and_audits(admin, run):
    response = admin.post(form_url(run))
    assert response.status_code == 303
    assert response.headers["Location"] == "/admin/allotment"
    page = admin.get(response.headers["Location"])
    assert page.mimetype == "text/html"
    assert b"Allotment results published successfully." in page.data
    assert b"Results are published" in page.data
    assert b"Fictional administrator 701" in page.data
    assert b"UTC" in page.data
    assert form_url(run).encode() not in page.data
    assert b'type="submit">Publish results' not in page.data
    entry = db.session.execute(db.select(AuditLog).filter_by(action_type="results.publish")).scalar_one()
    assert entry.actor_id == admin.user_id and entry.target_id == run.id


def test_existing_publication_shows_original_publisher_to_another_admin(app, admin, run):
    original = publish(run.id, admin.user_id)
    other = login_client(app, "administrator", 702)
    page = other.get("/admin/allotment").get_data(as_text=True)
    assert "Fictional administrator 701" in page
    assert f'action="{form_url(run)}"' not in page
    details = publication_details(run.id)
    assert details["published_at"] == original.published_at
    assert details["published_by"] == admin.user_id


def test_repeat_form_submission_explains_conflict_and_does_not_duplicate(admin, run):
    assert admin.post(form_url(run)).status_code == 303
    response = admin.post(form_url(run), follow_redirects=True)
    assert response.status_code == 200
    assert b"already been published" in response.data
    assert publication_count() == 1
    entries = db.session.execute(db.select(AuditLog).filter_by(action_type="results.publish")).scalars().all()
    assert len(entries) == 1


def test_unknown_run_explains_error_and_returns_to_console(admin):
    response = admin.post("/admin/allotment/runs/99999/publish", follow_redirects=True)
    assert response.status_code == 200
    assert b"No completed allotment run was found." in response.data
    assert publication_count() == 0


def test_anonymous_and_candidate_cannot_submit_form(app, admin, run):
    candidate = login_client(app, "candidate", 703)
    assert app.test_client().post(form_url(run)).status_code == 401
    assert candidate.post(form_url(run)).status_code == 403
    assert publication_count() == 0
    assert db.session.execute(db.select(AuditLog)).scalars().all() == []


def test_partial_uses_optional_shared_token_without_duplicate_fields(app, run):
    with app.test_request_context():
        page = render_template("results/_publish_card.html", run=run,
                               publication=None, report=[], csrf_token=lambda: "shared-test-token")
    assert page.count('name="csrf_token"') == 1
    assert 'value="shared-test-token"' in page


def test_partial_disables_button_for_consistency_mismatch(app, run):
    with app.test_request_context():
        page = render_template("results/_publish_card.html", run=run, publication=None,
                               report=[{"seat_id": 1}])
    assert "Resolve the seat consistency mismatches" in page
    assert 'type="button" disabled>Publish results' in page
    assert "<form" not in page


def test_publication_details_for_unknown_run_is_none(app):
    assert publication_details(99999) is None
