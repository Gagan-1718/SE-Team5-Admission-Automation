"""Fictional catalogue seed data, called by ``flask --app app seed-db``.

Safe to run repeatedly: colleges, branches and seat rows are looked up first and only
created when missing. Existing seat capacities are never overwritten, so numbers an
administrator has edited survive a re-seed.
"""
from app.extensions import db

from .models import Seat
from .services import create_branch, create_college, find_branch, find_college

# college name -> (city, {branch name: {category: capacity}})
SEED_COLLEGES = {
    "Meridian Institute of Technology": (
        "Lakeview",
        {
            "Computer Science and Engineering": {"General": 30, "OBC": 15, "SC": 8, "ST": 4, "EWS": 3},
            "Electronics and Communication Engineering": {"General": 24, "OBC": 12, "SC": 6, "ST": 3, "EWS": 3},
            "Mechanical Engineering": {"General": 18, "OBC": 9, "SC": 5, "ST": 2, "EWS": 2},
        },
    ),
    "Cedarwood College of Engineering": (
        "Hillcrest",
        {
            "Computer Science and Engineering": {"General": 20, "OBC": 10, "SC": 5, "ST": 3, "EWS": 2},
            "Information Science and Engineering": {"General": 16, "OBC": 8, "SC": 4, "ST": 2, "EWS": 2},
            "Civil Engineering": {"General": 12, "OBC": 6, "SC": 3, "ST": 2, "EWS": 1},
        },
    ),
}


def seed():
    """Create the fictional colleges, branches and seat rows that are missing."""
    for college_name, (city, branches) in SEED_COLLEGES.items():
        college = find_college(college_name) or create_college(college_name, city)
        for branch_name, capacities in branches.items():
            branch = find_branch(college, branch_name) or create_branch(college, branch_name)
            for category, capacity in capacities.items():
                if branch.seat_for(category) is None:
                    db.session.add(
                        Seat(branch_id=branch.id, category=category, capacity=capacity, filled=0)
                    )
            db.session.commit()
            db.session.refresh(branch)
