"""Candidate catalogue page: listing, filtering and seat-availability figures."""
from app.extensions import db
from tests.catalogue.helpers import get_college, get_seat

MERIDIAN = b"Meridian Institute of Technology"
CEDARWOOD = b"Cedarwood College of Engineering"


def test_catalogue_lists_all_colleges_and_branches(seeded, client):
    response = client.get("/colleges")
    assert response.status_code == 200
    assert MERIDIAN in response.data and CEDARWOOD in response.data
    for branch in (b"Mechanical Engineering", b"Civil Engineering", b"Information Science and Engineering"):
        assert branch in response.data


def test_empty_catalogue_shows_a_message(app, client):
    response = client.get("/colleges")
    assert response.status_code == 200
    assert b"No colleges or branches match" in response.data


def test_filter_by_branch_name_shows_only_matching_branches(seeded, client):
    response = client.get("/colleges?q=civil")
    assert b"Civil Engineering" in response.data
    assert CEDARWOOD in response.data
    assert MERIDIAN not in response.data
    assert b"Mechanical Engineering" not in response.data
    assert b"Information Science" not in response.data


def test_filter_by_college_name_shows_all_its_branches(seeded, client):
    response = client.get("/colleges?q=CEDARWOOD")
    assert CEDARWOOD in response.data
    for branch in (b"Computer Science and Engineering", b"Information Science and Engineering", b"Civil Engineering"):
        assert branch in response.data
    assert MERIDIAN not in response.data


def test_filter_matching_branches_in_several_colleges(seeded, client):
    response = client.get("/colleges?q=computer science")
    assert MERIDIAN in response.data and CEDARWOOD in response.data
    assert b"Civil Engineering" not in response.data
    assert b"Mechanical Engineering" not in response.data


def test_college_dropdown_filter(seeded, client):
    cedarwood_id = get_college("Cedarwood College of Engineering").id
    response = client.get(f"/colleges?college_id={cedarwood_id}")
    listing = response.data.split(b"<h2>")[1:]  # the headings of the result sections
    assert len(listing) == 1 and CEDARWOOD in listing[0]


def test_college_and_text_filters_combine(seeded, client):
    meridian_id = get_college("Meridian Institute of Technology").id
    response = client.get(f"/colleges?college_id={meridian_id}&q=civil")
    assert b"No colleges or branches match" in response.data


def test_filter_with_no_match_shows_message(seeded, client):
    response = client.get("/colleges?q=zzz-no-such-thing")
    assert b"No colleges or branches match" in response.data
    assert MERIDIAN not in response.data


def test_filter_text_is_not_treated_as_a_pattern(seeded, client):
    assert b"No colleges or branches match" in client.get("/colleges?q=%25").data
    assert b"No colleges or branches match" in client.get("/colleges?q=_").data


def test_filter_text_is_escaped_in_the_page(seeded, client):
    response = client.get("/colleges?q=<script>alert(1)</script>")
    assert b"<script>alert(1)</script>" not in response.data


def test_seat_availability_matches_the_seat_matrix(seeded, client):
    seat = get_seat("Meridian Institute of Technology", "Computer Science and Engineering", "General")
    seat.filled = 5
    db.session.commit()
    response = client.get("/colleges?q=meridian")
    assert b"25 / 30" in response.data  # General: 30 - 5 filled
    # whole-branch total: 30+15+8+4+3 = 60 capacity, 5 filled
    assert b"55 / 60" in response.data


def test_unset_category_is_shown_as_a_dash(app, client):
    from app.catalogue.services import create_branch, create_college, set_seat_capacity

    branch = create_branch(create_college("Test College One"), "Civil")
    set_seat_capacity(branch, "General", 7)
    response = client.get("/colleges")
    assert b"7 / 7" in response.data
    assert b"&ndash;" in response.data


def test_college_without_branches_is_listed_with_a_note(app, client):
    from app.catalogue.services import create_college

    create_college("Test College One")
    response = client.get("/colleges")
    assert b"Test College One" in response.data
    assert b"No branches have been added" in response.data
