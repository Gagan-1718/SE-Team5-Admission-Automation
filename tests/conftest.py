"""Shared pytest fixtures. Every test gets its own temporary SQLite file."""
import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-not-a-real-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + (tmp_path / "test.db").as_posix(),
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()  # release the file so Windows can delete it


@pytest.fixture
def client(app):
    return app.test_client()
