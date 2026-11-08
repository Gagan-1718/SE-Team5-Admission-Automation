"""ADM-F-019 / TC-019: exactly-once choices, audit atomicity, CSRF and concurrency."""
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from app.audit.models import AuditLog
from app.catalogue.models import Seat
from app.extensions import db
from app.results import services
from app.results.models import SeatDecision

API = "/api/v1/allotment/decision"


def publish(w):
    services.publish(w["run"].id, w["users"]["admin"].id)


def decisions():
    return db.session.execute(db.select(SeatDecision)).scalars().all()


def audit():
    return db.session.execute(db.select(AuditLog).filter_by(action_type="results.decision")).scalars().all()


@pytest.mark.parametrize("decision", ["Accepted", "Rejected"])
def test_service_records_once_without_altering_seat_usage(result_world, decision):
    w = result_world
    publish(w)
    before = [(s.id, s.filled, s.capacity) for s in db.session.execute(db.select(Seat)).scalars()]
    value = services.decide(w["users"]["allocated"].id, decision)
    assert value.decision == decision
    assert value.result_id == w["allocated"].id
    assert value.decided_at
    assert services.candidate_view(w["users"]["allocated"].id)["decision"]["decision"] == decision
    db.session.expire_all()
    assert [(s.id, s.filled, s.capacity) for s in db.session.execute(db.select(Seat)).scalars()] == before
    [entry] = audit()
    assert entry.actor_role == "candidate" and entry.target_id == w["allocated"].id


def test_decision_before_publication_is_refused(result_world):
    w = result_world
    with pytest.raises(services.NotPublished):
        services.decide(w["users"]["allocated"].id, "Accepted")
    assert decisions() == audit() == []


@pytest.mark.parametrize("key", ["not_allocated", "outsider"])
def test_no_allocated_seat_is_refused(result_world, key):
    w = result_world
    publish(w)
    with pytest.raises(services.NotAllocated):
        services.decide(w["users"][key].id, "Accepted")
    assert decisions() == audit() == []


@pytest.mark.parametrize("invalid", ["Accept", "", None, ["Accepted"], "Maybe"])
def test_invalid_service_decision_is_rejected(result_world, invalid):
    w = result_world
    publish(w)
    with pytest.raises(services.InvalidDecision):
        services.decide(w["users"]["allocated"].id, invalid)
    assert decisions() == []


def test_direct_administrator_service_call_is_refused(result_world):
    w = result_world
    publish(w)
    with pytest.raises(PermissionError):
        services.decide(w["users"]["admin"].id, "Accepted")
    assert decisions() == []


def test_second_decision_cannot_change_first(result_world):
    w = result_world
    publish(w)
    cid = w["users"]["allocated"].id
    services.decide(cid, "Accepted")
    with pytest.raises(services.AlreadyDecided, match="Your decision has already been recorded"):
        services.decide(cid, "Rejected")
    assert len(decisions()) == len(audit()) == 1
    assert decisions()[0].decision == "Accepted"


@pytest.mark.parametrize("failure", ["audit", "commit"])
def test_failure_rolls_back_decision_and_audit(result_world, monkeypatch, failure):
    w = result_world
    publish(w)

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated decision failure")

    if failure == "audit":
        monkeypatch.setattr(services, "record_audit", fail)
    else:
        monkeypatch.setattr(db.session, "commit", fail)
    with pytest.raises(RuntimeError, match="decision failure"):
        services.decide(w["users"]["allocated"].id, "Accepted")
    assert decisions() == audit() == []
    assert db.session.get(Seat, w["seat"].id).filled == 1


@pytest.mark.parametrize("choice,stored", [("Accept", "Accepted"), ("Reject", "Rejected")])
def test_api_uses_session_identity_and_returns_saved_decision(result_world, choice, stored):
    w = result_world
    publish(w)
    response = w["client"]().post(API, json={
        "decision": choice, "candidate_id": w["users"]["outsider"].id,
        "result_id": w["not_allocated"].id,
    })
    assert response.status_code == 201
    assert response.json["decision"] == stored
    assert decisions()[0].result_id == w["allocated"].id


@pytest.mark.parametrize("payload", [None, [], {"decision": "Accepted"}, {"decision": ["Accept"]}, {}])
def test_api_invalid_payload_is_400(result_world, payload):
    publish(result_world)
    assert result_world["client"]().post(API, json=payload).status_code == 400
    assert decisions() == []


def test_api_statuses_and_authorization(app, result_world):
    w = result_world
    client = w["client"]()
    assert client.post(API, json={"decision": "Accept"}).status_code == 404
    assert app.test_client().post(API, json={"decision": "Accept"}).status_code == 401
    assert w["client"]("admin").post(API, json={"decision": "Accept"}).status_code == 403
    publish(w)
    for key in ("outsider", "not_allocated"):
        assert w["client"](key).post(API, json={"decision": "Accept"}).status_code == 422
    assert client.post(API, json={"decision": "Accept"}).status_code == 201
    assert client.post(API, json={"decision": "Reject"}).status_code == 409


def test_browser_form_redirects_and_hides_buttons_after_decision(result_world):
    publish(result_world)
    client = result_world["client"]()
    response = client.post("/result/decision", data={"decision": "Reject"}, follow_redirects=True)
    assert response.status_code == 200 and response.mimetype == "text/html"
    assert b"Rejected" in response.data
    assert b"already been recorded" in response.data
    assert b"Accept seat</button>" not in response.data
    assert b"Reject seat</button>" not in response.data
    assert client.post("/result/decision", data={"decision": "Accept"}).status_code == 303
    assert decisions()[0].decision == "Rejected"


def test_central_csrf_blocks_missing_and_wrong_tokens(app, result_world):
    w = result_world
    publish(w)
    client = w["client"]()
    app.config["CSRF_ENABLED"] = True
    assert client.get("/result").status_code == 200
    assert client.post(API, json={"decision": "Accept"}).status_code == 400
    assert client.post(API, json={"decision": "Accept"},
                       headers={"X-CSRF-Token": "wrong"}).status_code == 400
    with client.session_transaction() as session:
        token = session["_csrf_token"]
    assert client.post("/result/decision", data={"decision": "Accept", "csrf_token": token}).status_code == 303


def test_two_authenticated_sessions_race_and_only_one_decision_wins(app, result_world, monkeypatch):
    w = result_world
    publish(w)
    clients = [w["client"](), w["client"]()]
    app.config["CSRF_ENABLED"] = True
    tokens = []
    for client in clients:
        assert client.get("/result").status_code == 200
        with client.session_transaction() as session:
            tokens.append(session["_csrf_token"])
    gate = Barrier(2)
    original = services._decision_for_result

    def read_together(result_id):
        value = original(result_id)
        if value is None:
            gate.wait(timeout=10)
        return value

    monkeypatch.setattr(services, "_decision_for_result", read_together)
    db.session.remove()

    def submit(index):
        response = clients[index].post(API, json={"decision": ["Accept", "Reject"][index]},
                                       headers={"X-CSRF-Token": tokens[index]})
        return response.status_code, response.json

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, n) for n in range(2)]
        outcomes = [future.result(timeout=25) for future in futures]
    assert sorted(status for status, _ in outcomes) == [201, 409], outcomes
    assert len(decisions()) == len(audit()) == 1
    assert db.session.execute(db.select(Seat).filter_by(id=w["seat"].id)).scalar_one().filled == 1


def test_console_summary_counts_allocated_seats_only(result_world):
    w = result_world
    publish(w)
    assert services.decision_summary(w["run"].id) == {"Accepted": 0, "Rejected": 0, "Undecided": 1}
    services.decide(w["users"]["allocated"].id, "Rejected")
    assert services.decision_summary(w["run"].id) == {"Accepted": 0, "Rejected": 1, "Undecided": 0}
    assert services.decision_summary(99999) == {"Accepted": 0, "Rejected": 0, "Undecided": 0}
    page = w["client"]("admin").get("/admin/allotment")
    assert page.status_code == 200
    assert b"Seat decisions" in page.data and b"Rejected seats are not released" in page.data


def test_result_page_shows_a_readable_decision_time(result_world):
    publish(result_world)
    client = result_world["client"]()
    before = client.get("/result").get_data(as_text=True)
    assert "does not release it" in before  # warn before the one-time choice
    page = client.post("/result/decision", data={"decision": "Accept"}, follow_redirects=True).get_data(as_text=True)
    assert "T" not in page.split("Recorded on ", 1)[1].split(" UTC", 1)[0]  # not raw ISO text
    assert re.search(r"Recorded on \d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2} UTC", page)
    assert "does not release it" not in page
