"""Allotment API and administrator console (issue #5 and the console issue; TC-015, TC-022, TC-025)."""
from app.allotment.models import AllotmentRun
from app.extensions import db
from tests.catalogue.helpers import login_client

API = "/api/v1/admin/allotment/run"


def runs():
    return db.session.query(AllotmentRun).count()


# ------------------------------------------------------------------ JSON API
def test_api_refuses_anonymous_and_candidates(app, oracle):
    assert app.test_client().post(API).status_code == 401
    assert login_client(app, "candidate", 501).post(API).status_code == 403
    assert runs() == 0


def test_api_runs_once_then_says_already_completed(app, oracle):
    admin = login_client(app, "administrator", 502)
    first = admin.post(API)
    assert first.status_code == 200
    body = first.get_json()
    assert (body["candidatesProcessed"], body["allocatedCount"], body["notAllocatedCount"]) == (5, 3, 2)
    assert body["runId"] and body["durationMs"] >= 0

    second = admin.post(API)
    assert second.status_code == 409
    assert second.get_json()["status"] == 409 and second.get_json()["message"]
    assert runs() == 1


def test_api_with_nobody_locked_is_422_and_saves_nothing(app, world):
    world.branch("A-CSE", {"General": 1})
    world.candidate("Open", 1, ["A-CSE"], locked=False)
    response = login_client(app, "administrator", 503).post(API)
    assert response.status_code == 422
    assert runs() == 0


def test_the_run_appears_in_the_audit_log(app, oracle):
    admin = login_client(app, "administrator", 504)
    admin.post(API)
    actions = [entry["actionType"] for entry in admin.get("/admin/audit-logs.json").get_json()]
    assert "allotment.run" in actions


# ------------------------------------------------------------------ console page
def test_console_refuses_anonymous_and_candidates_like_every_admin_route(app, oracle):
    assert app.test_client().get("/admin/allotment").status_code == 401
    assert app.test_client().post("/admin/allotment/run").status_code == 401
    candidate = login_client(app, "candidate", 505)
    assert candidate.get("/admin/allotment").status_code == 403
    assert candidate.post("/admin/allotment/run").status_code == 403
    assert runs() == 0


def test_console_before_the_run_shows_checks_and_an_enabled_run_button(app, oracle):
    page = login_client(app, "administrator", 506).get("/admin/allotment").get_data(as_text=True)
    assert "Pre-run checks" in page
    assert "5 ready" in page
    assert '<button class="btn primary" type="submit">Run allotment</button>' in page
    assert "cannot be repeated" in page


def test_console_disables_run_when_nobody_is_ready(app, world):
    world.branch("A-CSE", {"General": 1})
    world.candidate("Open", 1, ["A-CSE"], locked=False)
    page = login_client(app, "administrator", 507).get("/admin/allotment").get_data(as_text=True)
    assert "Not ready" in page
    assert '<button class="btn" type="submit" disabled>Run allotment</button>' in page


def test_running_from_the_console_shows_the_summary_and_locks_the_button(app, oracle):
    admin = login_client(app, "administrator", 508)
    response = admin.post("/admin/allotment/run")
    assert response.status_code == 303
    page = admin.get("/admin/allotment").get_data(as_text=True)
    assert "Allotment complete: 3 allocated, 2 not allocated." in page
    assert "Passed" in page and "0 mismatches" in page
    assert "Run allotment (already completed)" in page
    assert "Run completed, not published" in page
    assert "Oracle College A · CSE" in page
    assert runs() == 1


def test_a_second_run_from_the_console_explains_why(app, oracle):
    admin = login_client(app, "administrator", 509)
    admin.post("/admin/allotment/run")
    admin.post("/admin/allotment/run")
    page = admin.get("/admin/allotment").get_data(as_text=True)
    assert "There is one cycle only." in page
    assert runs() == 1
