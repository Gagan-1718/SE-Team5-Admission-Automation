"""Administrator candidate list (ADM-F-020): search, pages of 25, application status."""
from app.accounts.models import User
from app.application.models import Application
from app.extensions import db
from tests.catalogue.helpers import login_client


def add_candidates(count):
    for n in range(1, count + 1):
        db.session.add(User(name=f"Fictional Person {n:03d}", email=f"list{n:03d}@example.test",
                            mobile=f"91000{n:05d}", password_hash="not-a-real-hash", role="candidate"))
    db.session.commit()


def page_of(admin, query=""):
    return admin.get(f"/admin/candidates{query}").get_data(as_text=True)


def test_list_is_split_into_pages_of_25(app):
    admin = login_client(app, "administrator", 701)
    add_candidates(30)
    first = page_of(admin)
    assert "Fictional Person 001" in first and "Fictional Person 025" in first
    assert "Fictional Person 026" not in first
    assert "30 candidates" in first and "Page 1 of 2" in first
    second = page_of(admin, "?page=2")
    assert "Fictional Person 026" in second and "Fictional Person 001" not in second


def test_out_of_range_page_shows_the_last_page(app):
    admin = login_client(app, "administrator", 702)
    add_candidates(3)
    assert "Fictional Person 003" in page_of(admin, "?page=99")
    assert "Fictional Person 001" in page_of(admin, "?page=0")


def test_search_keeps_its_term_across_pages(app):
    admin = login_client(app, "administrator", 703)
    add_candidates(30)
    page = page_of(admin, "?q=Person+02")
    assert "Fictional Person 020" in page and "Fictional Person 001" not in page
    assert "10 candidates" in page


def test_application_status_and_reference_are_shown(app):
    admin = login_client(app, "administrator", 704)
    add_candidates(2)
    first = db.session.execute(db.select(User).filter_by(email="list001@example.test")).scalar_one()
    db.session.add(Application(candidate_id=first.id, status="Submitted", reference_number="ADM-2026-000777"))
    db.session.commit()
    page = page_of(admin)
    assert "ADM-2026-000777" in page and "Submitted" in page
    assert "Not started" in page


def test_only_administrators_can_open_the_list(app):
    assert app.test_client().get("/admin/candidates").status_code == 401
    assert login_client(app, "candidate", 705).get("/admin/candidates").status_code == 403
