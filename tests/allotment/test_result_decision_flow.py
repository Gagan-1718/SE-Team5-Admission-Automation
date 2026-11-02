
"""Appendix-B oracle through real allotment, publication, result and decision routes."""

import re

from app.accounts.security import hash_password
from app.allotment.services import seat_consistency_report
from app.extensions import db

PASSWORD = "fictional-cycle-password"


def login(app, user):
    client = app.test_client()
    page = client.get("/accounts/login").get_data(as_text=True)
    csrf = re.search(
        r'<meta name="csrf-token" content="([^"]+)"',
        page,
    ).group(1)

    response = client.post(
        "/accounts/login",
        json={
            "identifier": user.email,
            "password": PASSWORD,
        },
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 200, response.json
    return client, {"X-CSRF-Token": csrf}


def test_oracle_results_and_decisions_complete_the_real_http_flow(app, oracle):
    outsider = oracle.candidate(
        "NeverLocked",
        100,
        ["A-CSE"],
        locked=False,
    )

    hashed = hash_password(PASSWORD)

    for user in [oracle.admin, *oracle.candidates.values()]:
        user.password_hash = hashed

    db.session.commit()
    app.config["CSRF_ENABLED"] = True

    admin, admin_headers = login(app, oracle.admin)

    # Verify seat-matrix edits are recorded in the audit log.
    branch = oracle.branches["A-CSE"]

    seat_response = admin.post(
        f"/admin/branches/{branch.id}/seats",
        data={
            "General": "2",
            "OBC": "1",
            "SC": "0",
            "ST": "0",
            "EWS": "0",
        },
        headers=admin_headers,
    )


    assert seat_response.status_code in (302, 303)

    clients = {
        key: login(app, user)
        for key, user in oracle.candidates.items()
    }

    response = admin.post(
        "/api/v1/admin/allotment/run",
        headers=admin_headers,
    )
    assert response.status_code == 200, response.json

    run_id = response.json["runId"]

    c1, c1_headers = clients["C1"]

    hidden = c1.get("/api/v1/allotment/result")
    assert hidden.status_code == 404
    assert hidden.json["result"] is None

    assert admin.post(
        f"/admin/allotment/runs/{run_id}/publish",
        headers=admin_headers,
    ).status_code == 303

    expected = {
        "C1": ("Oracle College A", "CSE"),
        "C2": ("Oracle College A", "CSE"),
        "C3": ("Oracle College A", "ISE"),
    }

    for key, (client, _) in clients.items():
        response = client.get("/api/v1/allotment/result")

        assert response.status_code == 200

        page = client.get("/result")
        assert page.status_code == 200

        if key in expected:
            assert response.json["state"] == "ALLOCATED"

            assert (
                response.json["result"]["college"],
                response.json["result"]["branch"],
            ) == expected[key]

            assert b"Your allotted seat" in page.data

        elif key in ("C4", "C5"):
            assert response.json["state"] == "NOT_ALLOCATED"
            assert "college" not in response.json["result"]
            assert b"None of your locked choices" in page.data

        else:
            assert response.json["state"] == "NOT_IN_RUN"

    assert c1.post(
        "/api/v1/allotment/decision",
        json={"decision": "Reject"},
        headers=c1_headers,
    ).status_code == 201

    assert c1.post(
        "/api/v1/allotment/decision",
        json={"decision": "Accept"},
        headers=c1_headers,
    ).status_code == 409

    c2, c2_headers = clients["C2"]

    assert c2.post(
        "/api/v1/allotment/decision",
        json={"decision": "Accept"},
        headers=c2_headers,
    ).status_code == 201

    for key in ("C4", "C5", "NeverLocked"):
        client, headers = clients[key]

        assert client.post(
            "/api/v1/allotment/decision",
            json={"decision": "Accept"},
            headers=headers,
        ).status_code == 422

    assert oracle.seat("A-CSE").filled == 2
    assert seat_consistency_report() == []

    actions = [
        entry["actionType"]
        for entry in admin.get("/admin/audit-logs.json").json
    ]

    assert "seats.update" in actions
    assert "allotment.run" in actions
    assert "results.publish" in actions
    assert actions.count("results.decision") == 2

    summary = admin.get("/admin/allotment").get_data(as_text=True)
    assert "Seat decisions" in summary

    assert (
        c1.get("/api/v1/allotment/result").json["decision"]["decision"]
        == "Rejected"
    )

    assert (
        "Accept seat</button>"
        not in c1.get("/result").get_data(as_text=True)
    )
