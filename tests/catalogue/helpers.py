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


# ---- real logins (shared by the catalogue, eligibility, admin and audit tests)
PASSWORD = "fictional-password-1"


def login_client(app, role, number):
    """Create a user with the given role and return a test client signed in as them."""
    from app.accounts.models import User
    from app.accounts.security import hash_password

    email = f"{role}.{number}@example.test"
    user = User(name=f"Fictional {role} {number}", email=email, mobile=f"90000{number:05d}",
                role=role, password_hash=hash_password(PASSWORD))
    db.session.add(user)
    db.session.commit()
    client = app.test_client()
    response = client.post("/accounts/login", json={"identifier": email, "password": PASSWORD})
    assert response.status_code == 200
    client.user_id = user.id
    return client
