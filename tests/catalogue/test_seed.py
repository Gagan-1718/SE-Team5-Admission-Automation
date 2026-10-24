"""The seed routine creates fictional data and is safe to run repeatedly."""
from app.catalogue.models import SEAT_CATEGORIES, Branch, College, Seat
from app.catalogue.seed import SEED_COLLEGES, seed
from app.extensions import db

from tests.catalogue.helpers import count, get_seat


def expected_counts():
    branches = sum(len(data[1]) for data in SEED_COLLEGES.values())
    seats = sum(len(caps) for data in SEED_COLLEGES.values() for caps in data[1].values())
    return len(SEED_COLLEGES), branches, seats


def test_seed_creates_two_colleges_with_several_branches_and_all_categories(app):
    seed()
    assert count(College) == 2
    assert count(Branch) >= 4
    for branch in db.session.execute(db.select(Branch)).scalars():
        assert {s.category for s in branch.seats} == set(SEAT_CATEGORIES)
        assert all(s.capacity >= 0 and s.filled == 0 for s in branch.seats)


def test_seed_is_idempotent(app):
    seed()
    first = (count(College), count(Branch), count(Seat))
    seed()
    seed()
    assert (count(College), count(Branch), count(Seat)) == first == expected_counts()


def test_reseed_keeps_admin_edited_capacity(seeded):
    seat = get_seat("Meridian Institute of Technology", "Mechanical Engineering", "General")
    seat.capacity = 99
    db.session.commit()
    seed()
    db.session.expire_all()
    seat = get_seat("Meridian Institute of Technology", "Mechanical Engineering", "General")
    assert seat.capacity == 99
    assert count(Seat) == expected_counts()[2]


def test_reseed_restores_a_missing_seat_row_without_duplicates(seeded):
    seat = get_seat("Cedarwood College of Engineering", "Civil Engineering", "EWS")
    db.session.delete(seat)
    db.session.commit()
    seed()
    db.session.expire_all()
    assert count(Seat) == expected_counts()[2]
    assert get_seat("Cedarwood College of Engineering", "Civil Engineering", "EWS").capacity == 1


def test_seed_db_command_is_repeatable_and_reports_catalogue(app):
    runner = app.test_cli_runner()
    for _ in range(2):
        result = runner.invoke(args=["seed-db"])
        assert result.exit_code == 0, result.output
    assert "Seeded catalogue." in result.output
    db.session.expire_all()
    assert (count(College), count(Branch), count(Seat)) == expected_counts()
