"""Administrator pages: add/edit colleges, branches and seat capacity."""
from app.catalogue.models import Branch, College, Seat
from app.extensions import db

from tests.catalogue.helpers import count, get_branch, get_college, get_seat
import pytest


@pytest.fixture
def admin_access(app):
    app.config["CATALOGUE_ADMIN_GUARD"] = lambda: True
    return app
MERIDIAN = "Meridian Institute of Technology"
CSE = "Computer Science and Engineering"


def test_admin_index_lists_seeded_catalogue(seeded, admin_access, client):
    response = client.get("/admin/colleges")
    assert response.status_code == 200
    assert MERIDIAN.encode() in response.data
    assert b"Cedarwood College of Engineering" in response.data
    assert b"Add college" in response.data


def test_add_college(admin_access, client):
    response = client.post("/admin/colleges/new", data={"name": "Test College One", "city": "Testville"})
    assert response.status_code == 302
    db.session.expire_all()
    college = get_college("Test College One")
    assert college.city == "Testville"
    page = client.get(response.headers["Location"])
    assert b"College &#39;Test College One&#39; added." in page.data


def test_add_duplicate_college_is_rejected_with_message(admin_access, client):
    client.post("/admin/colleges/new", data={"name": "Test College One"})
    response = client.post("/admin/colleges/new", data={"name": "  test college ONE "})
    assert response.status_code == 409
    assert b"already exists" in response.data
    db.session.expire_all()
    assert count(College) == 1


def test_add_college_with_blank_name_is_rejected(admin_access, client):
    response = client.post("/admin/colleges/new", data={"name": "   ", "city": "X"})
    assert response.status_code == 422
    assert b"College name is required." in response.data
    assert count(College) == 0


def test_edit_college(seeded, admin_access, client):
    college = get_college(MERIDIAN)
    response = client.post(
        f"/admin/colleges/{college.id}/edit", data={"name": "Meridian Tech Institute", "city": "Newtown"}
    )
    assert response.status_code == 302
    db.session.expire_all()
    edited = db.session.get(College, college.id)
    assert (edited.name, edited.city) == ("Meridian Tech Institute", "Newtown")


def test_edit_college_form_is_prefilled(seeded, admin_access, client):
    college = get_college(MERIDIAN)
    response = client.get(f"/admin/colleges/{college.id}/edit")
    assert response.status_code == 200
    assert MERIDIAN.encode() in response.data


def test_edit_college_to_duplicate_name_is_rejected_and_unchanged(seeded, admin_access, client):
    college = get_college(MERIDIAN)
    response = client.post(
        f"/admin/colleges/{college.id}/edit",
        data={"name": "cedarwood college of engineering", "city": "Lakeview"},
    )
    assert response.status_code == 409
    db.session.expire_all()
    assert db.session.get(College, college.id).name == MERIDIAN


def test_edit_college_keeping_own_name_is_allowed(seeded, admin_access, client):
    college = get_college(MERIDIAN)
    response = client.post(f"/admin/colleges/{college.id}/edit", data={"name": MERIDIAN, "city": "Elsewhere"})
    assert response.status_code == 302
    db.session.expire_all()
    assert db.session.get(College, college.id).city == "Elsewhere"


def test_add_branch_then_set_seats(admin_access, client):
    client.post("/admin/colleges/new", data={"name": "Test College One"})
    db.session.expire_all()
    college = get_college("Test College One")

    response = client.post(f"/admin/colleges/{college.id}/branches/new", data={"name": "Civil Engineering"})
    assert response.status_code == 302
    db.session.expire_all()
    branch = get_branch("Test College One", "Civil Engineering")
    assert response.headers["Location"].endswith(f"/admin/branches/{branch.id}/seats")

    response = client.post(
        f"/admin/branches/{branch.id}/seats",
        data={"General": "20", "OBC": "10", "SC": "5", "ST": "2", "EWS": ""},
    )
    assert response.status_code == 302
    db.session.expire_all()
    assert get_seat("Test College One", "Civil Engineering", "General").capacity == 20
    assert get_seat("Test College One", "Civil Engineering", "ST").capacity == 2
    assert count(Seat) == 4  # blank EWS means "not set"


def test_add_duplicate_branch_is_rejected(seeded, admin_access, client):
    college = get_college(MERIDIAN)
    before = count(Branch)
    response = client.post(f"/admin/colleges/{college.id}/branches/new", data={"name": "computer science and engineering"})
    assert response.status_code == 409
    assert b"already has a branch" in response.data
    db.session.expire_all()
    assert count(Branch) == before


def test_rename_branch_and_reject_duplicate_rename(seeded, admin_access, client):
    branch = get_branch(MERIDIAN, "Mechanical Engineering")
    ok = client.post(f"/admin/branches/{branch.id}/edit", data={"name": "Mechanical and Automation"})
    assert ok.status_code == 302
    clash = client.post(f"/admin/branches/{branch.id}/edit", data={"name": CSE})
    assert clash.status_code == 409
    db.session.expire_all()
    assert db.session.get(Branch, branch.id).name == "Mechanical and Automation"


def test_edit_seat_capacity(seeded, admin_access, client):
    branch = get_branch(MERIDIAN, CSE)
    response = client.post(
        f"/admin/branches/{branch.id}/seats",
        data={"General": "45", "OBC": "15", "SC": "8", "ST": "4", "EWS": "3"},
    )
    assert response.status_code == 302
    db.session.expire_all()
    assert get_seat(MERIDIAN, CSE, "General").capacity == 45


def test_negative_seat_capacity_is_rejected_and_nothing_is_saved(seeded, admin_access, client):
    branch = get_branch(MERIDIAN, CSE)
    response = client.post(
        f"/admin/branches/{branch.id}/seats",
        data={"General": "60", "OBC": "-3", "SC": "8", "ST": "4", "EWS": "3"},
    )
    assert response.status_code == 422
    assert b"cannot be negative" in response.data
    db.session.expire_all()
    assert get_seat(MERIDIAN, CSE, "General").capacity == 30  # valid field not saved either
    assert get_seat(MERIDIAN, CSE, "OBC").capacity == 15


def test_non_numeric_seat_capacity_is_rejected(seeded, admin_access, client):
    branch = get_branch(MERIDIAN, CSE)
    response = client.post(f"/admin/branches/{branch.id}/seats", data={"General": "lots"})
    assert response.status_code == 422
    assert b"whole number" in response.data


def test_seat_capacity_below_filled_is_rejected(seeded, admin_access, client):
    seat = get_seat(MERIDIAN, CSE, "General")
    seat.filled = 10
    db.session.commit()
    branch = get_branch(MERIDIAN, CSE)
    response = client.post(f"/admin/branches/{branch.id}/seats", data={"General": "5"})
    assert response.status_code == 422
    assert b"already filled" in response.data
    db.session.expire_all()
    assert get_seat(MERIDIAN, CSE, "General").capacity == 30


def test_unknown_records_return_404(admin_access, client):
    assert client.get("/admin/colleges/999/edit").status_code == 404
    assert client.post("/admin/colleges/999/branches/new", data={"name": "X"}).status_code == 404
    assert client.get("/admin/branches/999/edit").status_code == 404
    assert client.get("/admin/branches/999/seats").status_code == 404


def test_admin_pages_use_the_configurable_guard(seeded, client):
    seeded.config["CATALOGUE_ADMIN_GUARD"] = lambda: False
    college = get_college(MERIDIAN)
    for path in (
        "/admin/colleges",
        "/admin/colleges/new",
        f"/admin/colleges/{college.id}/edit",
    ):
        assert client.get(path).status_code == 403
    assert client.post("/admin/colleges/new", data={"name": "Sneaky College"}).status_code == 403
    db.session.expire_all()
    assert count(College) == 2
    assert client.get("/colleges").status_code == 200  # candidate page stays public

def test_admin_colleges_denies_access_when_guard_is_missing(seeded, client):
    seeded.config.pop("CATALOGUE_ADMIN_GUARD", None)

    response = client.get("/admin/colleges")

    assert response.status_code == 403

def test_admin_pages_allow_an_admin_guard(seeded, client):
    seeded.config["CATALOGUE_ADMIN_GUARD"] = lambda: True
    assert client.get("/admin/colleges").status_code == 200


def test_new_record_appears_for_candidates_immediately(admin_access, client):
    client.post("/admin/colleges/new", data={"name": "Test College One", "city": "Testville"})
    db.session.expire_all()
    college = get_college("Test College One")
    client.post(f"/admin/colleges/{college.id}/branches/new", data={"name": "Civil Engineering"})
    db.session.expire_all()
    branch = get_branch("Test College One", "Civil Engineering")
    client.post(f"/admin/branches/{branch.id}/seats", data={"General": "12"})
    page = client.get("/colleges")
    assert b"Test College One" in page.data
    assert b"Civil Engineering" in page.data
    assert b"12 / 12" in page.data
