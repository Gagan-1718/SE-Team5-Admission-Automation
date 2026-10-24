"""Models and business rules: duplicates, negative capacity, relationships, DB constraints."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.catalogue.models import Branch, CatalogueError, College, DuplicateError, Seat
from app.catalogue.services import (
    create_branch,
    create_college,
    set_branch_seats,
    set_seat_capacity,
)
from app.extensions import db

from tests.catalogue.helpers import count


def test_college_branch_seat_relationships(app):
    college = create_college("Test College One", "Testville")
    branch = create_branch(college, "Test Branch")
    set_seat_capacity(branch, "General", 10)
    set_seat_capacity(branch, "SC", 4)
    db.session.expire_all()

    saved = db.session.get(College, college.id)
    assert [b.name for b in saved.branches] == ["Test Branch"]
    assert saved.branches[0].college is saved
    assert {s.category: s.capacity for s in saved.branches[0].seats} == {"General": 10, "SC": 4}
    assert saved.seats_total == 14
    assert saved.seats_available == 14


def test_duplicate_college_is_rejected_ignoring_case_and_spaces(app):
    create_college("Test College One")
    with pytest.raises(DuplicateError):
        create_college("Test College One")
    with pytest.raises(DuplicateError):
        create_college("  test   COLLEGE one ")
    assert count(College) == 1


def test_duplicate_college_is_also_blocked_by_the_database(app):
    db.session.add(College(name="Test College One"))
    db.session.commit()
    db.session.add(College(name="TEST COLLEGE ONE"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_duplicate_branch_in_same_college_is_rejected(app):
    college = create_college("Test College One")
    create_branch(college, "Computer Science")
    with pytest.raises(DuplicateError):
        create_branch(college, "computer  science")
    assert count(Branch) == 1


def test_same_branch_name_is_allowed_in_different_colleges(app):
    first = create_college("Test College One")
    second = create_college("Test College Two")
    create_branch(first, "Computer Science")
    create_branch(second, "Computer Science")
    assert count(Branch) == 2


def test_duplicate_branch_is_also_blocked_by_the_database(app):
    college = create_college("Test College One")
    db.session.add(Branch(college_id=college.id, name="Civil"))
    db.session.commit()
    db.session.add(Branch(college_id=college.id, name="CIVIL"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_blank_and_overlong_names_are_rejected(app):
    with pytest.raises(CatalogueError):
        create_college("   ")
    with pytest.raises(CatalogueError):
        create_college("x" * 121)
    college = create_college("Test College One")
    with pytest.raises(CatalogueError):
        create_branch(college, "")


def test_negative_seat_capacity_is_rejected(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    with pytest.raises(CatalogueError, match="negative"):
        set_seat_capacity(branch, "General", -1)
    with pytest.raises(CatalogueError, match="negative"):
        Seat(branch_id=branch.id, category="General", capacity=-5)
    assert count(Seat) == 0


def test_negative_capacity_is_also_blocked_by_the_database(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    with pytest.raises(IntegrityError):
        db.session.execute(
            text(
                "INSERT INTO catalogue_seat (branch_id, category, capacity, filled) "
                "VALUES (:b, 'General', -1, 0)"
            ),
            {"b": branch.id},
        )
    db.session.rollback()


def test_filled_cannot_exceed_capacity_in_the_database(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    with pytest.raises(IntegrityError):
        db.session.execute(
            text(
                "INSERT INTO catalogue_seat (branch_id, category, capacity, filled) "
                "VALUES (:b, 'General', 3, 4)"
            ),
            {"b": branch.id},
        )
    db.session.rollback()


@pytest.mark.parametrize("bad", ["abc", "1.5", "", None, True, 2.5])
def test_non_whole_number_capacity_is_rejected(app, bad):
    branch = create_branch(create_college("Test College One"), "Civil")
    with pytest.raises(CatalogueError):
        set_seat_capacity(branch, "General", bad)


def test_zero_capacity_is_allowed(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    assert set_seat_capacity(branch, "General", 0).capacity == 0


def test_unknown_category_is_rejected_and_case_is_normalised(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    with pytest.raises(CatalogueError):
        set_seat_capacity(branch, "Management", 5)
    assert set_seat_capacity(branch, "general", 5).category == "General"


def test_setting_capacity_twice_updates_one_row(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    set_seat_capacity(branch, "General", 5)
    set_seat_capacity(branch, "General", 9)
    assert count(Seat) == 1
    assert db.session.execute(db.select(Seat.capacity)).scalar() == 9


def test_duplicate_seat_row_is_blocked_by_the_database(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    db.session.add(Seat(branch_id=branch.id, category="General", capacity=5))
    db.session.commit()
    db.session.add(Seat(branch_id=branch.id, category="General", capacity=6))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_capacity_cannot_drop_below_filled_seats(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    seat = set_seat_capacity(branch, "General", 10)
    seat.filled = 6  # simulates the later allotment module
    db.session.commit()
    with pytest.raises(CatalogueError, match="already filled"):
        set_seat_capacity(branch, "General", 5)
    assert set_seat_capacity(branch, "General", 6).capacity == 6


def test_set_branch_seats_is_all_or_nothing(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    with pytest.raises(CatalogueError):
        set_branch_seats(branch, {"General": "10", "OBC": "-2", "SC": "x"})
    db.session.expire_all()
    assert count(Seat) == 0


def test_seat_availability_is_capacity_minus_filled(app):
    branch = create_branch(create_college("Test College One"), "Civil")
    seat = set_seat_capacity(branch, "General", 10)
    seat.filled = 4
    db.session.commit()
    assert seat.available == 6
    assert branch.seats_available == 6


def test_foreign_keys_are_enforced_for_branches(app):
    db.session.add(Branch(college_id=9999, name="Orphan"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_deleting_a_college_removes_its_branches_and_seats(app):
    college = create_college("Test College One")
    branch = create_branch(college, "Civil")
    set_seat_capacity(branch, "General", 5)
    db.session.delete(college)
    db.session.commit()
    assert count(College) == count(Branch) == count(Seat) == 0
