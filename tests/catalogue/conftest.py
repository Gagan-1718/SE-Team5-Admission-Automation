"""Catalogue test fixtures. The shared ``app`` and ``client`` fixtures come from tests/conftest.py,
so every test uses its own temporary SQLite file."""
import pytest

from app.catalogue.seed import seed
from app.extensions import db


@pytest.fixture
def seeded(app):
    """An app whose database already holds the fictional catalogue seed data."""
    seed()
    db.session.expire_all()
    return app
