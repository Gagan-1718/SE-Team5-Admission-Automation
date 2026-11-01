"""Tests for the eligibility candidate journey step."""

import pytest

from app.eligibility import journey
from app.eligibility.evaluation import PENDING, ELIGIBLE, NOT_ELIGIBLE
from app.journey import WAITING, DONE, PROBLEM


@pytest.mark.parametrize(
    ("eligibility_status", "expected_state"),
    [
        (PENDING, WAITING),
        (NOT_ELIGIBLE, PROBLEM),
        (ELIGIBLE, DONE),
    ],
)
def test_eligibility_status_maps_to_journey_state(
    monkeypatch, eligibility_status, expected_state
):
    reason = "Test eligibility reason."

    monkeypatch.setattr(
        journey,
        "get_eligibility",
        lambda candidate_id: {
            "status": eligibility_status,
            "reason": reason,
        },
    )

    steps = journey.step_statuses(123)

    assert len(steps) == 1
    assert steps[0]["key"] == "eligibility"
    assert steps[0]["label"] == "Eligibility"
    assert steps[0]["state"] == expected_state
    assert steps[0]["detail"] == reason
    assert steps[0]["href"] == "/eligibility"


def test_unknown_eligibility_status_raises_error(monkeypatch):
    monkeypatch.setattr(
        journey,
        "get_eligibility",
        lambda candidate_id: {
            "status": "Unknown",
            "reason": "Unknown status.",
        },
    )

    with pytest.raises(ValueError, match="Unknown eligibility status"):
        journey.step_statuses(123)


def test_candidate_id_is_passed_to_eligibility_service(monkeypatch):
    received = []

    def fake_get_eligibility(candidate_id):
        received.append(candidate_id)
        return {"status": PENDING, "reason": "Awaiting verification."}

    monkeypatch.setattr(journey, "get_eligibility", fake_get_eligibility)

    journey.step_statuses(456)

    assert received == [456]
