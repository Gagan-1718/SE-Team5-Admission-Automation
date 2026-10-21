"""Catalogue models: College -> Branch -> Seat (one row per category).

Owner: Tasya. Business rules enforced here AND in the database:
  * college names are unique (case-insensitive, extra spaces ignored)
  * branch names are unique inside one college (same rule)
  * one seat row per branch + category
  * seat capacity and filled seats are whole numbers, never negative,
    and filled can never exceed capacity
"""
from sqlalchemy import CheckConstraint, Index, UniqueConstraint, func
from sqlalchemy.orm import validates

from app.extensions import db

# Agreed fictional category list. Eligibility/allotment will match on these exact names.
SEAT_CATEGORIES = ("General", "OBC", "SC", "ST", "EWS")

NAME_MAX = 120
CITY_MAX = 80


class CatalogueError(ValueError):
    """A catalogue business rule was broken (message is safe to show to the admin)."""


class DuplicateError(CatalogueError):
    """A college or branch with that name already exists."""


def clean_text(value, label, max_len, required=True):
    """Trim, collapse inner spaces and check length. Returns the cleaned string."""
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise CatalogueError(f"{label} must be text.")
    cleaned = " ".join(value.split())
    if required and not cleaned:
        raise CatalogueError(f"{label} is required.")
    if len(cleaned) > max_len:
        raise CatalogueError(f"{label} must be at most {max_len} characters.")
    return cleaned


def clean_category(value):
    """Return the canonical category name, or raise CatalogueError."""
    if isinstance(value, str):
        wanted = value.strip().casefold()
        for category in SEAT_CATEGORIES:
            if category.casefold() == wanted:
                return category
    raise CatalogueError("Category must be one of: " + ", ".join(SEAT_CATEGORIES) + ".")


def clean_count(value, label):
    """Accept a whole number (int, or digits in a string). Reject negatives and junk."""
    if isinstance(value, bool):
        raise CatalogueError(f"{label} must be a whole number.")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise CatalogueError(f"{label} is required.")
        try:
            value = int(text)
        except ValueError:
            raise CatalogueError(f"{label} must be a whole number.") from None
    if not isinstance(value, int):
        raise CatalogueError(f"{label} must be a whole number.")
    if value < 0:
        raise CatalogueError(f"{label} cannot be negative.")
    return value


class College(db.Model):
    __tablename__ = "catalogue_college"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_MAX), nullable=False)
    city = db.Column(db.String(CITY_MAX), nullable=False, default="")

    branches = db.relationship(
        "Branch",
        back_populates="college",
        cascade="all, delete-orphan",
        order_by="Branch.name",
    )

    __table_args__ = (Index("uq_catalogue_college_name_ci", func.lower(name), unique=True),)

    @validates("name")
    def _validate_name(self, key, value):
        return clean_text(value, "College name", NAME_MAX)

    @validates("city")
    def _validate_city(self, key, value):
        return clean_text(value, "City", CITY_MAX, required=False)

    @property
    def seats_total(self):
        return sum(branch.seats_total for branch in self.branches)

    @property
    def seats_available(self):
        return sum(branch.seats_available for branch in self.branches)

    def __repr__(self):
        return f"<College {self.name!r}>"


class Branch(db.Model):
    __tablename__ = "catalogue_branch"

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(
        db.Integer,
        db.ForeignKey("catalogue_college.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(NAME_MAX), nullable=False)

    college = db.relationship("College", back_populates="branches")
    seats = db.relationship(
        "Seat",
        back_populates="branch",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("uq_catalogue_branch_name_ci", college_id, func.lower(name), unique=True),
    )

    @validates("name")
    def _validate_name(self, key, value):
        return clean_text(value, "Branch name", NAME_MAX)

    def seat_for(self, category):
        """The Seat row for a category, or None if none has been configured."""
        for seat in self.seats:
            if seat.category == category:
                return seat
        return None

    @property
    def seats_sorted(self):
        order = {name: index for index, name in enumerate(SEAT_CATEGORIES)}
        return sorted(self.seats, key=lambda seat: order.get(seat.category, 99))

    @property
    def seats_total(self):
        return sum(seat.capacity for seat in self.seats)

    @property
    def seats_available(self):
        return sum(seat.available for seat in self.seats)

    def __repr__(self):
        return f"<Branch {self.name!r} college_id={self.college_id}>"


class Seat(db.Model):
    """Category-wise seat capacity for one branch (one row of the seat matrix).

    ``filled`` is reserved for the later allotment module; the catalogue never
    changes it, it only guarantees ``0 <= filled <= capacity``.
    """

    __tablename__ = "catalogue_seat"

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(
        db.Integer,
        db.ForeignKey("catalogue_branch.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=0)
    filled = db.Column(db.Integer, nullable=False, default=0)

    branch = db.relationship("Branch", back_populates="seats")

    __table_args__ = (
        UniqueConstraint("branch_id", "category", name="uq_catalogue_seat_branch_category"),
        CheckConstraint("capacity >= 0", name="ck_catalogue_seat_capacity_nonneg"),
        CheckConstraint("filled >= 0", name="ck_catalogue_seat_filled_nonneg"),
        CheckConstraint("filled <= capacity", name="ck_catalogue_seat_filled_within_capacity"),
    )

    @validates("category")
    def _validate_category(self, key, value):
        return clean_category(value)

    @validates("capacity")
    def _validate_capacity(self, key, value):
        return clean_count(value, "Seat capacity")

    @validates("filled")
    def _validate_filled(self, key, value):
        return clean_count(value, "Filled seats")

    @property
    def available(self):
        return (self.capacity or 0) - (self.filled or 0)

    def __repr__(self):
        return f"<Seat branch_id={self.branch_id} {self.category} {self.capacity}>"
