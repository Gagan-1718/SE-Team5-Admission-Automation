from app.choices import journey


def test_pending_and_not_eligible_candidates_have_locked_choices(monkeypatch):
    monkeypatch.setattr(journey, "get_eligibility", lambda candidate_id: {
        "status": "Pending", "reason": "Documents are under review."
    })
    assert journey.step_statuses(1)[0]["state"] == "locked"
    assert "Documents" in journey.step_statuses(1)[0]["detail"]

    monkeypatch.setattr(journey, "get_eligibility", lambda candidate_id: {
        "status": "Not Eligible", "reason": "Rank is outside the cut-off."
    })
    assert journey.step_statuses(1)[0]["state"] == "locked"


def test_eligible_open_choices_are_current(monkeypatch):
    monkeypatch.setattr(journey, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "Rank is within the cut-off."
    })
    monkeypatch.setattr(journey, "is_locked", lambda candidate_id: False)
    step = journey.step_statuses(1)[0]
    assert step == {
        "key": "choices",
        "label": "Choices",
        "state": "current",
        "detail": "Add and order your preferred college branches.",
        "href": "/choices",
    }


def test_eligible_locked_choices_are_done(monkeypatch):
    monkeypatch.setattr(journey, "get_eligibility", lambda candidate_id: {
        "status": "Eligible", "reason": "Rank is within the cut-off."
    })
    monkeypatch.setattr(journey, "is_locked", lambda candidate_id: True)
    step = journey.step_statuses(1)[0]
    assert step["state"] == "done"
    assert "locked" in step["detail"]
