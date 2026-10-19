"""Application draft rules: validation, create and save (owner: Gagan).

Other modules should call these functions rather than touching the table.
Submission and reference numbers are issue #3 and are not implemented here.
"""
import math
import re

from sqlalchemy.exc import IntegrityError

from app.extensions import db

from .models import DRAFT, FORM_FIELDS, Application

BOARDS = ("Karnataka State PUC", "CBSE", "ICSE", "Other")
MAX_LENGTHS = {"guardian_name": 100, "school_name": 150}
MOBILE_PATTERN = re.compile(r"^\d{10}$")


class ValidationError(Exception):
    def __init__(self, errors):
        super().__init__("Some fields are invalid.")
        self.errors = errors  # {field_name: message}


class ApplicationExists(Exception):
    """The candidate already has an application (one per candidate)."""


class ApplicationLocked(Exception):
    """The application is already Submitted and can no longer be edited."""


def clean_fields(data):
    """Validate the fields that were supplied; partial drafts are allowed.

    Returns a dict containing only the supplied fields (blank text becomes None).
    Unknown keys such as status or candidate_id are ignored on purpose.
    """
    cleaned, errors = {}, {}
    for name in FORM_FIELDS:
        if name not in data:
            continue
        value = data[name]
        if isinstance(value, str):
            value = value.strip() or None
        if value is None:
            cleaned[name] = None
            continue

        if name in MAX_LENGTHS:
            if not isinstance(value, str) or len(value) > MAX_LENGTHS[name]:
                errors[name] = f"Must be text of at most {MAX_LENGTHS[name]} characters."
                continue
        elif name == "guardian_mobile":
            if not isinstance(value, str) or not MOBILE_PATTERN.match(value):
                errors[name] = "Enter a 10-digit mobile number."
                continue
        elif name == "board":
            if value not in BOARDS:
                errors[name] = "Choose one of: " + ", ".join(BOARDS) + "."
                continue
        elif name == "percentage":
            try:
                number = float(value)
            except (TypeError, ValueError):
                errors[name] = "Enter a number between 0 and 100."
                continue
            if isinstance(value, bool) or not math.isfinite(number) or not 0 <= number <= 100:
                errors[name] = "Enter a number between 0 and 100."
                continue
            value = number
        cleaned[name] = value

    if errors:
        raise ValidationError(errors)
    return cleaned


def get_for_candidate(candidate_id):
    return db.session.execute(
        db.select(Application).filter_by(candidate_id=candidate_id)
    ).scalar_one_or_none()


def create_draft(candidate_id, data):
    """Create the candidate's single draft. Raises ApplicationExists if one exists."""
    cleaned = clean_fields(data)
    if get_for_candidate(candidate_id) is not None:
        raise ApplicationExists()
    application = Application(candidate_id=candidate_id, status=DRAFT, **cleaned)
    db.session.add(application)
    try:
        db.session.commit()
    except IntegrityError:  # two requests raced; the unique constraint decides
        db.session.rollback()
        raise ApplicationExists()
    return application


def update_draft(application, data):
    """Save supplied fields onto an existing Draft. Raises ApplicationLocked once Submitted."""
    if not application.is_draft:
        raise ApplicationLocked()
    cleaned = clean_fields(data)
    for name, value in cleaned.items():
        setattr(application, name, value)
    db.session.commit()
    return application


def save_draft(candidate_id, data):
    """Create the draft if the candidate has none, otherwise update it (used by the form page)."""
    existing = get_for_candidate(candidate_id)
    if existing is None:
        return create_draft(candidate_id, data)
    return update_draft(existing, data)
