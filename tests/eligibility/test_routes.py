"""get_eligibility, the candidate page and the JSON endpoint (temporary inputs)."""
import pytest

from app.eligibility import services
from app.eligibility.seed import seed


@pytest.fixture(autouse=True)
def seeded_rules(app):
    seed()


def _use_inputs(monkeypatch, rank, category, documents_approved):
    monkeypatch.setattr(
        services,
        "_temporary_inputs",
        lambda candidate_id: {"rank": rank, "category": category, "documents_approved": documents_approved},
    )


def test_get_eligibility_default_temporary_inputs_is_eligible():
    result = services.get_eligibility(1)
    assert result == {"status": "Eligible", "reason": "Rank 1000 is within the General cut-off of 20000."}


def test_get_eligibility_pending(monkeypatch):
    _use_inputs(monkeypatch, 1000, "General", False)
    assert services.get_eligibility(1)["status"] == "Pending"


def test_get_eligibility_not_eligible(monkeypatch):
    _use_inputs(monkeypatch, 90000, "General", True)
    assert services.get_eligibility(1)["status"] == "Not Eligible"


def test_page_shows_status_and_reason(client):
    response = client.get("/eligibility")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Eligible" in page
    assert "Rank 1000 is within the General cut-off of 20000." in page


def test_page_shows_pending(client, monkeypatch):
    _use_inputs(monkeypatch, 1000, "General", False)
    page = client.get("/eligibility").get_data(as_text=True)
    assert "Pending" in page
    assert "Required documents are not all approved yet." in page


def test_json_endpoint(client):
    response = client.get("/api/v1/candidates/me/eligibility")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "Eligible",
        "reason": "Rank 1000 is within the General cut-off of 20000.",
    }


def test_json_endpoint_not_eligible(client, monkeypatch):
    _use_inputs(monkeypatch, 90000, "General", True)
    body = client.get("/api/v1/candidates/me/eligibility").get_json()
    assert body["status"] == "Not Eligible"
    assert body["reason"] == "Rank 90000 is above the General cut-off of 20000."


def test_eligibility_module_does_not_import_accounts_or_documents():
    import pathlib
    import re

    folder = pathlib.Path(services.__file__).parent
    pattern = re.compile(r"^\s*(from|import)\s+app\.(accounts|documents)", re.MULTILINE)
    for path in folder.glob("*.py"):
        assert not pattern.search(path.read_text(encoding="utf-8")), path.name
