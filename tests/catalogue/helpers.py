"""Small query helpers shared by the catalogue tests (imported as tests.catalogue.helpers)."""
from app.catalogue.models import Branch, College, Seat
from app.extensions import db


def get_college(name):
    return db.session.execute(db.select(College).filter_by(name=name)).scalar_one()


def get_branch(college_name, branch_name):
    college = get_college(college_name)
    return db.session.execute(
        db.select(Branch).filter_by(college_id=college.id, name=branch_name)
    ).scalar_one()


def get_seat(college_name, branch_name, category):
    branch = get_branch(college_name, branch_name)
    return db.session.execute(
        db.select(Seat).filter_by(branch_id=branch.id, category=category)
    ).scalar_one()


def count(model):
    return db.session.execute(db.select(db.func.count(model.id))).scalar()
