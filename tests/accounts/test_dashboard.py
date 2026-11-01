from app.accounts.models import ExamRecord, User
from app.extensions import db

from .test_registration import registration_payload


JOURNEY_LABELS = (
    "Profile and exam details",
    "Application",
    "Documents",
    "Eligibility",
    "Choices",
    "Allotment result",
    "Seat decision",
)


def register_and_login(client, email="candidate@example.test"):
    payload = registration_payload(email=email)
    assert client.post("/accounts/register", json=payload).status_code == 201
    assert client.post(
        "/accounts/login",
        json={"identifier": email, "password": payload["password"]},
    ).status_code == 200


def test_anonymous_dashboard_redirects_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/accounts/login?next=/dashboard" in response.headers["Location"]


def test_candidate_dashboard_has_seven_steps_and_summary(client):
    register_and_login(client)
    response = client.get("/dashboard")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert body.count("step-dot") == 7
    assert "Profile and exam details" in body
    assert "Documents approved" in body
    assert "Enter your exam details to continue." in body


def test_administrator_is_denied_dashboard(client, app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "fictional-admin-password")
    from app.accounts.seed import seed
    with app.app_context():
        seed()
    assert client.post(
        "/accounts/login",
        json={"identifier": "admin@example.test", "password": "fictional-admin-password"},
    ).status_code == 200
    assert client.get("/dashboard").status_code == 403


def test_dashboard_uses_monkeypatched_journey_and_selects_problem_first(client, monkeypatch):
    register_and_login(client)
    fake_steps = [
        {"key": "profile", "label": "Profile and exam details", "state": "current", "detail": "current", "href": "/accounts/profile-page"},
        {"key": "application", "label": "Application", "state": "problem", "detail": "fix this", "href": "/application"},
    ] + [
        {"key": str(i), "label": f"Step {i}", "state": "locked", "detail": "later", "href": "/"}
        for i in range(5)
    ]
    monkeypatch.setattr("app.accounts.routes.all_steps", lambda candidate_id: fake_steps)
    body = client.get("/dashboard").get_data(as_text=True)
    assert "fix this" in body
    assert "Open Application" in body


def test_dashboard_uses_first_problem_when_multiple_steps_need_attention(client, monkeypatch):
    steps = _scenario_steps(
        {
            "profile": "done",
            "application": "problem",
            "documents": "problem",
            "eligibility": "locked",
            "choices": "locked",
            "result": "locked",
            "decision": "locked",
        },
        {
            "application": "Application needs correction.",
            "documents": "Documents need correction.",
        },
        {"application": "/application", "documents": "/documents"},
    )
    body = _render_scenario(client, monkeypatch, steps)
    assert "Application needs correction." in body
    assert "Documents need correction." in body
    assert "Open Application" in body
    assert "Open Documents" not in body


def test_dashboard_uses_first_current_when_no_problem_exists(client, monkeypatch):
    steps = _scenario_steps(
        {
            "profile": "done",
            "application": "current",
            "documents": "current",
            "eligibility": "locked",
            "choices": "locked",
            "result": "locked",
            "decision": "locked",
        },
        {
            "application": "Complete your application.",
            "documents": "Upload your documents.",
        },
        {"application": "/application", "documents": "/documents"},
    )
    body = _render_scenario(client, monkeypatch, steps)
    assert "Open Application" in body
    assert "Open Documents" not in body


def test_dashboard_shows_status_without_action_when_no_step_is_actionable(client, monkeypatch):
    steps = _scenario_steps(
        {key: "done" for key in ("profile", "application", "documents", "eligibility", "choices", "result", "decision")},
        {key: "Complete" for key in ("profile", "application", "documents", "eligibility", "choices", "result", "decision")},
    )
    body = _render_scenario(client, monkeypatch, steps)
    assert "Journey status" in body
    assert "Next step" not in body
    assert "Open Profile and exam details" not in body


def test_login_rejects_external_next_but_keeps_local_next(client):
    external = client.get("/accounts/login?next=https://example.test/steal").get_data(as_text=True)
    protocol_relative = client.get("/accounts/login?next=//example.test/steal").get_data(as_text=True)
    local = client.get("/accounts/login?next=/application").get_data(as_text=True)
    assert 'https://example.test/steal' not in external
    assert '//example.test/steal' not in protocol_relative
    assert 'const requestedNext = "/application"' in local


def test_login_template_has_role_specific_dashboard_destinations(client):
    body = client.get("/accounts/login").get_data(as_text=True)
    assert '"/admin/dashboard"' in body
    assert '"/dashboard"' in body
    assert "/admin/documents" not in body


def _scenario_steps(states, details=None, hrefs=None):
    details = details or {}
    hrefs = hrefs or {}
    return [
        {
            "key": key,
            "label": label,
            "state": states[key],
            "detail": details.get(key, f"{label} detail"),
            "href": hrefs.get(key, f"/{key}"),
        }
        for key, label in zip(
            ("profile", "application", "documents", "eligibility", "choices", "result", "decision"),
            JOURNEY_LABELS,
        )
    ]


def _assert_ordered_seven_steps(body):
    assert body.count("step-dot") == 7
    stepper = body[body.index('<ol class="stepper">'):body.index("</ol>")]
    positions = [stepper.index(label) for label in JOURNEY_LABELS]
    assert positions == sorted(positions)


def _render_scenario(client, monkeypatch, steps):
    register_and_login(client, email="scenario@example.test")
    monkeypatch.setattr("app.accounts.routes.all_steps", lambda candidate_id: steps)
    return client.get("/dashboard").get_data(as_text=True)


def test_dashboard_scenario_brand_new_candidate(client, monkeypatch):
    steps = _scenario_steps(
        {key: "locked" for key in ("application", "documents", "eligibility", "choices", "result", "decision")}
        | {"profile": "current"},
        {"profile": "Enter your exam details to continue."},
        {"profile": "/accounts/profile-page"},
    )
    body = _render_scenario(client, monkeypatch, steps)
    _assert_ordered_seven_steps(body)
    assert "Enter your exam details to continue." in body
    assert "Open Profile and exam details" in body
    assert 'href="/accounts/profile-page"' in body
    assert "Not entered" in body and "Not started" in body


def test_dashboard_scenario_rejected_document_is_next_action(client, monkeypatch):
    steps = _scenario_steps(
        {"profile": "done", "application": "done", "documents": "problem", "eligibility": "locked", "choices": "locked", "result": "locked", "decision": "locked"},
        {"documents": "Rejected: blurred marksheet; upload a replacement."},
        {"documents": "/documents"},
    )
    body = _render_scenario(client, monkeypatch, steps)
    _assert_ordered_seven_steps(body)
    assert "Rejected: blurred marksheet; upload a replacement." in body
    assert "Open Documents" in body
    assert 'href="/documents"' in body


def test_dashboard_scenario_waiting_for_eligibility_has_no_wrong_action(client, monkeypatch):
    steps = _scenario_steps(
        {"profile": "done", "application": "done", "documents": "done", "eligibility": "waiting", "choices": "locked", "result": "locked", "decision": "locked"},
        {"eligibility": "Waiting for the eligibility decision."},
    )
    body = _render_scenario(client, monkeypatch, steps)
    _assert_ordered_seven_steps(body)
    assert "Waiting for the eligibility decision." in body
    assert "Journey status" in body
    assert "Next step" not in body


def test_dashboard_scenario_eligible_candidate_is_sent_to_choices(client, monkeypatch):
    steps = _scenario_steps(
        {"profile": "done", "application": "done", "documents": "done", "eligibility": "done", "choices": "current", "result": "locked", "decision": "locked"},
        {"choices": "Your eligibility is confirmed; fill your choices."},
        {"choices": "/choices"},
    )
    body = _render_scenario(client, monkeypatch, steps)
    _assert_ordered_seven_steps(body)
    assert "Open Choices" in body
    assert 'href="/choices"' in body


def test_dashboard_scenario_locked_choices_are_not_an_action(client, monkeypatch):
    steps = _scenario_steps(
        {"profile": "done", "application": "done", "documents": "done", "eligibility": "done", "choices": "done", "result": "locked", "decision": "locked"},
        {"choices": "Choices locked permanently in saved order."},
    )
    body = _render_scenario(client, monkeypatch, steps)
    _assert_ordered_seven_steps(body)
    assert "Choices locked permanently in saved order." in body
    assert "Journey status" in body
    assert "Open Choices" not in body


def test_dashboard_scenario_published_unallocated_result_has_no_accept_action(client, monkeypatch):
    steps = _scenario_steps(
        {"profile": "done", "application": "done", "documents": "done", "eligibility": "done", "choices": "done", "result": "problem", "decision": "done"},
        {"result": "No seat was allocated; no acceptance is required.", "decision": "No seat decision is available."},
        {"result": "/result", "decision": "/result"},
    )
    body = _render_scenario(client, monkeypatch, steps)
    _assert_ordered_seven_steps(body)
    assert "No seat was allocated; no acceptance is required." in body
    assert "Problem" in body
    assert "Open Allotment result" in body
    assert "Open Seat decision" not in body


def test_dashboard_scenario_allotted_result_prompts_for_seat_decision(client, monkeypatch):
    steps = _scenario_steps(
        {"profile": "done", "application": "done", "documents": "done", "eligibility": "done", "choices": "done", "result": "done", "decision": "current"},
        {"result": "You were allotted a seat.", "decision": "Record your accept or reject decision."},
        {"decision": "/result"},
    )
    body = _render_scenario(client, monkeypatch, steps)
    _assert_ordered_seven_steps(body)
    assert "You were allotted a seat." in body
    assert "Record your accept or reject decision." in body
    assert "Open Seat decision" in body
    assert 'href="/result"' in body
