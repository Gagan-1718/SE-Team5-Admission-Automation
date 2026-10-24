"""Fixtures for audit log tests."""
import pytest


@pytest.fixture
def seeded(app):
    """Seed the test database with the application's demo data."""
    result = app.test_cli_runner().invoke(args=["seed-db"])
    assert result.exit_code == 0, result.output
    return app
