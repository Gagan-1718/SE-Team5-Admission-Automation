"""ADM-F-018 / TC-018: publication gating, four outcomes and private result views."""
import pytest

from app.extensions import db
from app.results import services
from app.results.journey import step_statuses


def publish(w):
    return services.publish(w["run"].id, w["users"]["admin"].id)


def test_no_run_returns_only_unpublished_state(app):
    assert services.candidate_view(999) == {
        "state": "NOT_PUBLISHED", "result": None, "decision": None}


def test_existing_allocation_is_hidden_until_published(result_world):
    w = result_world
    view = services.candidate_view(w["users"]["allocated"].id)
    assert view["state"] == "NOT_PUBLISHED"
    assert view["result"] is view["decision"] is None


@pytest.mark.parametrize("key,state", [
    ("allocated", "ALLOCATED"), ("not_allocated", "NOT_ALLOCATED"), ("outsider", "NOT_IN_RUN"),
])
def test_published_service_states(result_world, key, state):
    publish(result_world)
    assert services.candidate_view(result_world["users"][key].id)["state"] == state


def test_letter_uses_snapshot_rank_and_candidate_exam(result_world):
    w = result_world
    publish(w)
    w["users"]["allocated"].rank = 99999
    db.session.commit()
    result = services.candidate_view(w["users"]["allocated"].id)["result"]
    assert result["rank"] == 1000
    assert result["exam_type"] == "KCET"
    assert result["reference_number"] == "ADM-2026-000001"
    assert result["choice_priority"] == 1 and result["total_choices"] == 2
    assert result["college"] == w["branch"].college.name
    assert result["category"] == "General"


def test_unallocated_result_never_contains_college_or_branch(result_world):
    publish(result_world)
    view = services.candidate_view(result_world["users"]["not_allocated"].id)
    assert "college" not in view["result"] and "branch" not in view["result"]
    assert view["decision"] is None


def test_page_is_informative_but_api_is_404_before_publication(result_world):
    client = result_world["client"]()
    page = client.get("/result")
    assert page.status_code == 200
    assert b"once the administrator publishes" in page.data
    assert b"ADM-2026-000001" not in page.data
    api = client.get("/api/v1/allotment/result")
    assert api.status_code == 404
    assert api.json["state"] == "NOT_PUBLISHED" and api.json["result"] is None


@pytest.mark.parametrize("key,state", [
    ("allocated", "ALLOCATED"), ("not_allocated", "NOT_ALLOCATED"), ("outsider", "NOT_IN_RUN"),
])
def test_published_page_and_api(result_world, key, state):
    w = result_world
    publish(w)
    client = w["client"](key)
    assert client.get("/result").status_code == 200
    response = client.get("/api/v1/allotment/result")
    assert response.status_code == 200
    assert response.json["state"] == state
    assert "no-store" in response.headers["Cache-Control"]


def test_query_string_cannot_select_another_candidates_result(result_world):
    w = result_world
    publish(w)
    other_id = w["users"]["allocated"].id
    for key in ("not_allocated", "outsider"):
        client = w["client"](key)
        api = client.get(f"/api/v1/allotment/result?candidate_id={other_id}")
        page = client.get(f"/result?candidate_id={other_id}")
        assert b"ADM-2026-000001" not in api.data + page.data
        assert b"Fictional allocated" not in api.data + page.data


def test_anonymous_and_admin_cannot_read_candidate_result(app, result_world):
    assert app.test_client().get("/result").status_code == 302
    assert app.test_client().get("/api/v1/allotment/result").status_code == 401
    admin = result_world["client"]("admin")
    assert admin.get("/result").status_code == 403
    assert admin.get("/api/v1/allotment/result").status_code == 403


def test_print_letter_and_confirmation_forms(result_world):
    publish(result_world)
    page = result_world["client"]().get("/result").get_data(as_text=True)
    assert "Your allotted seat" in page and "Choice 1 of 2" in page
    assert "window.print()" in page and "css/results.css" in page
    assert page.count('name="csrf_token"') == 2
    assert "Accept this allotted seat?" in page and "Reject this allotted seat?" in page
    assert "does not release it" in page
    assert "You can decide only once" in page


def test_result_pages_escape_candidate_content(result_world):
    w = result_world
    w["users"]["allocated"].name = '<script>alert("test")</script>'
    db.session.commit()
    publish(w)
    page = w["client"]().get("/result").get_data(as_text=True)
    assert '<script>alert("test")</script>' not in page
    assert "&lt;script&gt;" in page


def test_print_css_hides_shell_and_buttons():
    from pathlib import Path
    css = Path("static/css/results.css").read_text()
    assert "@media print" in css and "@page" in css
    for selector in (".app-sidebar", ".app-topbar", ".no-print", ".result-ticket"):
        assert selector in css


def test_journey_changes_after_publication_and_decision(result_world):
    w = result_world
    cid = w["users"]["allocated"].id
    assert [step["state"] for step in step_statuses(cid)] == ["locked", "locked"]
    publish(w)
    assert [step["state"] for step in step_statuses(cid)] == ["done", "current"]
    services.decide(cid, "Accepted")
    assert [step["state"] for step in step_statuses(cid)] == ["done", "done"]


@pytest.mark.parametrize("key", ["not_allocated", "outsider"])
def test_no_seat_journey_is_problem_and_decision_locked(result_world, key):
    publish(result_world)
    assert [step["state"] for step in step_statuses(result_world["users"][key].id)] == ["problem", "locked"]
