"""The module list used for auto-discovery (models, routes, seeds)."""
import importlib

from app import MODULES


def test_every_registered_module_package_exists():
    for name in MODULES:
        assert importlib.import_module(f"app.{name}") is not None


def test_audit_and_admin_modules_are_registered(app):
    assert "audit" in MODULES
    assert "admin" in MODULES
    assert client_can_start(app)


def client_can_start(app):
    return app.test_client().get("/health").status_code == 200
