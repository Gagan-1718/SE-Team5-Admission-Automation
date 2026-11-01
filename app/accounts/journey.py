"""Accounts-owned journey step for the candidate dashboard."""
from app.extensions import db
from app.journey import DONE, CURRENT, make_step

from .models import User


def step_statuses(candidate_id):
    user = db.session.get(User, candidate_id)
    if user is None or user.exam_record_id is None:
        return [make_step(
            "profile",
            "Profile and exam details",
            CURRENT,
            "Enter your exam details to continue.",
            "/accounts/profile-page",
        )]
    return [make_step(
        "profile",
        "Profile and exam details",
        DONE,
        "Your exam details are saved.",
        "/accounts/profile-page",
    )]
