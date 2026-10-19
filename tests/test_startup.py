"""Startup, health, database and discovery checks for the shared foundation (#31)."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from app import import_optional
from app.extensions import db
from app.setup_check import FICTIONAL_LABEL, SetupCheck, seed


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Admission Automation" in response.data


def test_static_stylesheet_is_served(client):
    assert client.get("/static/css/site.css").status_code == 200


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "ok"}


def test_health_reports_error_when_database_is_down(client, monkeypatch):
    def broken_execute(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("database unavailable"))

    monkeypatch.setattr(db.session, "execute", broken_execute)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.get_json() == {"status": "error", "database": "unavailable"}


def test_fictional_record_can_be_saved_and_read(app):
    db.session.add(SetupCheck(label="fictional demo row"))
    db.session.commit()
    db.session.expire_all()

    saved = db.session.execute(
        db.select(SetupCheck).filter_by(label="fictional demo row")
    ).scalar_one()
    assert saved.id is not None
    assert saved.created_at is not None


def test_seed_is_repeatable(app):
    seed()
    seed()
    rows = db.session.execute(db.select(SetupCheck)).scalars().all()
    assert [row.label for row in rows] == [FICTIONAL_LABEL]


def test_sqlite_foreign_keys_are_enabled(app):
    assert db.session.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_foreign_key_violation_is_rejected(app):
    db.session.execute(text("CREATE TABLE parent_demo (id INTEGER PRIMARY KEY)"))
    db.session.execute(
        text(
            "CREATE TABLE child_demo (id INTEGER PRIMARY KEY, "
            "parent_id INTEGER NOT NULL REFERENCES parent_demo(id))"
        )
    )
    with pytest.raises(IntegrityError):
        db.session.execute(text("INSERT INTO child_demo (id, parent_id) VALUES (1, 999)"))
    db.session.rollback()


def test_cli_commands_are_repeatable(app):
    runner = app.test_cli_runner()
    for _ in range(2):
        init_result = runner.invoke(args=["init-db"])
        seed_result = runner.invoke(args=["seed-db"])
        assert init_result.exit_code == 0, init_result.output
        assert seed_result.exit_code == 0, seed_result.output
    assert "Database tables are ready." in init_result.output
    assert db.session.execute(db.select(db.func.count(SetupCheck.id))).scalar() == 1


def test_missing_module_files_are_ignored():
    assert import_optional("app.no_such_module.models") is None
    assert import_optional("app.setup_check.no_such_file") is None


def test_broken_module_import_is_not_hidden(tmp_path, monkeypatch):
    (tmp_path / "broken_module_demo.py").write_text(
        "import a_package_that_does_not_exist_xyz\n", encoding="utf-8"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(ModuleNotFoundError):
        import_optional("broken_module_demo")
