"""Whole-cycle dashboard figures, including the negative outcomes (R1-4, ADM-F-020)."""
import pytest

from app.admin.services import cycle_overview
from app.allotment.services import run_allotment
from scripts import make_demo_dataset as generator
from tests.catalogue.helpers import login_client


@pytest.fixture
def demo_world(app, tmp_path, monkeypatch):
    """30 generated candidates: 24 eligible (21 locked, 3 open), 3 pending, 3 not eligible."""
    from app.catalogue.seed import seed as seed_catalogue
    from app.eligibility.seed import seed as seed_eligibility

    monkeypatch.setattr(generator, "upload_directory", lambda: tmp_path / "uploads")
    monkeypatch.setenv("DEMO_CANDIDATE_PASSWORD", "test-demo-password")
    seed_catalogue()
    seed_eligibility()
    generator.generate_dataset(30, 1)
    return app


def parts(split):
    return {p["label"]: p["count"] for p in split["parts"]}


def test_overview_counts_every_outcome_before_the_run(demo_world):
    o = cycle_overview()
    assert o["total"] == 30
    assert parts(o["eligibility"]) == {"Eligible": 24, "Pending": 3, "Not eligible": 3}
    assert parts(o["choices"]) == {"Locked": 21, "Saved, not locked": 3, "No choices yet": 0}
    assert parts(o["applications"]) == {"Submitted": 30, "Draft": 0, "Not started": 0}
    docs = parts(o["documents"])
    assert docs["Approved"] + docs["Pending"] + docs["Rejected"] == 90 and docs["Approved"] == 87
    assert o["allotment"] is None and o["decisions"] is None and o["published"] is False
    pipeline = {p["label"]: p["count"] for p in o["pipeline"]}
    assert pipeline["Registered"] == 30 and pipeline["Eligible"] == 24 and pipeline["Choices locked"] == 21
    assert sum(s["capacity"] for s in o["seats"]) > 0 and all(s["filled"] == 0 for s in o["seats"])


def test_overview_after_the_run_splits_allotted_not_allotted_and_not_in_run(demo_world):
    admin = login_client(demo_world, "administrator", 801)
    run_allotment(admin.user_id)
    o = cycle_overview()
    allotment = parts(o["allotment"])
    assert allotment["Allocated"] + allotment["Not allocated"] == 21
    assert allotment["Not in the run"] == 9
    assert parts(o["decisions"]) == {"Accepted": 0, "Undecided": allotment["Allocated"], "Rejected": 0}
    assert sum(s["filled"] for s in o["seats"]) == allotment["Allocated"]


def test_dashboard_page_shows_the_figures_and_negative_cases(demo_world):
    page = login_client(demo_world, "administrator", 802).get("/admin/dashboard").get_data(as_text=True)
    for text in ("Admission pipeline", "Not eligible", "Saved, not locked", "Rejected", "Seats by college",
                 "RV College of Engineering"):
        assert text in page
