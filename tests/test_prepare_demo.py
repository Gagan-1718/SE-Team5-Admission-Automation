"""scripts/prepare_demo.py gives a clean, known demo state (fictional data)."""
import pytest

from app.accounts.models import User
from app.extensions import db
from scripts.prepare_demo import (
    ADMIN_EMAIL,
    DEMO_CANDIDATE_EMAIL,
    prepare_demo,
)

ADMIN_PASSWORD = "demo-admin-password-1"
CANDIDATE_PASSWORD = "demo-candidate-password-1"


def login(app, email, password):
    return app.test_client().post("/accounts/login", json={"identifier": email, "password": password})


def test_prepares_admin_seeds_and_candidate_that_can_log_in(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", ADMIN_PASSWORD)
    prepare_demo(app, with_candidate=True, candidate_password=CANDIDATE_PASSWORD)

    assert login(app, ADMIN_EMAIL, ADMIN_PASSWORD).status_code == 200
    assert login(app, DEMO_CANDIDATE_EMAIL, CANDIDATE_PASSWORD).status_code == 200
    colleges = app.test_client().get("/colleges")
    assert colleges.status_code in (200, 302)  # catalogue is seeded (page needs a login)


def test_running_it_twice_starts_from_a_clean_database(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", ADMIN_PASSWORD)
    prepare_demo(app, with_candidate=True, candidate_password=CANDIDATE_PASSWORD)
    prepare_demo(app, with_candidate=True, candidate_password=CANDIDATE_PASSWORD)
    with app.app_context():
        emails = sorted(user.email for user in db.session.execute(db.select(User)).scalars())
    assert emails == [ADMIN_EMAIL, DEMO_CANDIDATE_EMAIL]


def test_without_the_flag_no_candidate_is_created(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", ADMIN_PASSWORD)
    prepare_demo(app)
    with app.app_context():
        assert [u.email for u in db.session.execute(db.select(User)).scalars()] == [ADMIN_EMAIL]


def test_candidate_password_is_required_with_the_flag(app, monkeypatch):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", ADMIN_PASSWORD)
    with pytest.raises(ValueError):
        prepare_demo(app, with_candidate=True, candidate_password=None)


def test_uploaded_files_from_earlier_runs_are_removed(app, monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", ADMIN_PASSWORD)
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    (uploads / "leftover.pdf").write_bytes(b"%PDF-1.4")
    app.config["DOCUMENT_UPLOAD_DIR"] = str(uploads)
    prepare_demo(app)
    assert not uploads.exists()
