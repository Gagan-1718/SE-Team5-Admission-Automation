"""Catalogue business operations shared by the routes, the seed routine and the tests.

Every function either completes and commits, or raises CatalogueError/DuplicateError
after rolling back, so a failed admin action never leaves half-saved data.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.extensions import db

from .models import (
    NAME_MAX,
    SEAT_CATEGORIES,
    Branch,
    CatalogueError,
    College,
    DuplicateError,
    Seat,
    clean_category,
    clean_count,
    clean_text,
)


# ----------------------------------------------------------------- lookups
def find_college(name):
    key = " ".join((name or "").split()).casefold()
    return db.session.execute(
        db.select(College).where(db.func.lower(College.name) == key)
    ).scalar_one_or_none()


def find_branch(college, name):
    key = " ".join((name or "").split()).casefold()
    return db.session.execute(
        db.select(Branch).where(
            Branch.college_id == college.id, db.func.lower(Branch.name) == key
        )
    ).scalar_one_or_none()


def _commit(duplicate_message):
    """Commit; turn a unique-index race into a friendly DuplicateError."""
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise DuplicateError(duplicate_message) from None


# ---------------------------------------------------------------- colleges
def create_college(name, city=""):
    name = clean_text(name, "College name", NAME_MAX)
    city = clean_text(city, "City", 80, required=False)
    if find_college(name) is not None:
        raise DuplicateError(f"A college named '{name}' already exists.")
    college = College(name=name, city=city)
    db.session.add(college)
    _commit(f"A college named '{name}' already exists.")
    return college


def update_college(college, name, city=""):
    name = clean_text(name, "College name", NAME_MAX)
    city = clean_text(city, "City", 80, required=False)
    other = find_college(name)
    if other is not None and other.id != college.id:
        raise DuplicateError(f"A college named '{name}' already exists.")
    college.name = name
    college.city = city
    _commit(f"A college named '{name}' already exists.")
    return college


# ---------------------------------------------------------------- branches
def create_branch(college, name):
    name = clean_text(name, "Branch name", NAME_MAX)
    if find_branch(college, name) is not None:
        raise DuplicateError(f"{college.name} already has a branch named '{name}'.")
    branch = Branch(college_id=college.id, name=name)
    db.session.add(branch)
    _commit(f"{college.name} already has a branch named '{name}'.")
    return branch


def update_branch(branch, name):
    name = clean_text(name, "Branch name", NAME_MAX)
    other = find_branch(branch.college, name)
    if other is not None and other.id != branch.id:
        raise DuplicateError(f"{branch.college.name} already has a branch named '{name}'.")
    branch.name = name
    _commit(f"{branch.college.name} already has a branch named '{name}'.")
    return branch


# ------------------------------------------------------------------- seats
def set_seat_capacity(branch, category, capacity):
    """Create or update one category row. Cannot go below seats already filled."""
    category = clean_category(category)
    capacity = clean_count(capacity, "Seat capacity")
    seat = branch.seat_for(category)
    if seat is None:
        seat = Seat(branch_id=branch.id, category=category, capacity=capacity, filled=0)
        db.session.add(seat)
    else:
        if capacity < seat.filled:
            raise CatalogueError(
                f"{category} capacity cannot be lower than the {seat.filled} seats already filled."
            )
        seat.capacity = capacity
    _commit(f"A {category} seat row already exists for this branch.")
    return seat


def set_branch_seats(branch, raw_capacities):
    """Save several categories at once (the admin seat form), all or nothing.

    ``raw_capacities`` maps category -> text/int. Blank text means "leave as is".
    Raises CatalogueError listing every problem and saves nothing if any value is bad.
    """
    problems = []
    planned = []
    for category in SEAT_CATEGORIES:
        raw = raw_capacities.get(category)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        try:
            capacity = clean_count(raw, f"{category} capacity")
        except CatalogueError as exc:
            problems.append(str(exc))
            continue
        seat = branch.seat_for(category)
        if seat is not None and capacity < seat.filled:
            problems.append(
                f"{category} capacity cannot be lower than the {seat.filled} seats already filled."
            )
            continue
        planned.append((category, capacity))
    if problems:
        raise CatalogueError(" ".join(problems))
    for category, capacity in planned:
        seat = branch.seat_for(category)
        if seat is None:
            db.session.add(Seat(branch_id=branch.id, category=category, capacity=capacity, filled=0))
        else:
            seat.capacity = capacity
    _commit("Seat rows could not be saved because of a duplicate category.")
    db.session.refresh(branch)
    return branch


# ------------------------------------------------------- candidate catalogue
def list_catalogue(query=None, college_id=None):
    """Colleges (with branches) for the candidate page.

    * ``college_id`` limits the list to one college.
    * ``query`` is a case-insensitive text filter: a college whose name matches is shown
      with all its branches; otherwise only the branches whose name matches are shown.
    Returns a list of (college, [branches]) pairs ordered by name; colleges with
    nothing left to show are dropped.
    """
    stmt = (
        db.select(College)
        .options(selectinload(College.branches).selectinload(Branch.seats))
        .order_by(db.func.lower(College.name))
    )
    if college_id:
        stmt = stmt.where(College.id == college_id)
    colleges = db.session.execute(stmt).scalars().all()

    needle = " ".join((query or "").split()).casefold()
    result = []
    for college in colleges:
        branches = sorted(college.branches, key=lambda b: b.name.casefold())
        if needle and needle not in college.name.casefold():
            branches = [b for b in branches if needle in b.name.casefold()]
            if not branches:
                continue
        result.append((college, branches))
    return result
