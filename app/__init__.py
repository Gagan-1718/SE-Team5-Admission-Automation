"""Team 5 Admission Automation application package (application factory).

Module owners plug in without editing this file. For each module listed in
MODULES, the factory looks for these optional files:

    app/<module>/models.py   SQLAlchemy models (imported so tables are created)
    app/<module>/routes.py   a Flask Blueprint named ``bp`` (registered automatically)
    app/<module>/seed.py     a ``seed()`` function used by ``flask seed-db``
"""
import importlib
import os
from pathlib import Path

from flask import Flask

from config import Config, load_or_create_secret_key

from .extensions import db

# One owner per module (see the sprint guide). Order is also the seed order.
MODULES = ("accounts", "application", "documents", "catalogue", "eligibility")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def import_optional(dotted_path):
    """Import a module if it exists; return None if it has not been written yet.

    Only a missing module (or one of its parent packages) is ignored. A broken
    import inside an existing module still raises so real bugs are not hidden.
    """
    try:
        return importlib.import_module(dotted_path)
    except ModuleNotFoundError as exc:
        if exc.name and (dotted_path == exc.name or dotted_path.startswith(exc.name + ".")):
            return None
        raise


def create_app(config_overrides=None):
    app = Flask(
        __name__,
        instance_path=str(PROJECT_ROOT / "instance"),
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    os.makedirs(app.instance_path, exist_ok=True)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = load_or_create_secret_key(app.instance_path)

    db.init_app(app)

    from .main import bp as main_bp

    app.register_blueprint(main_bp)

    for name in MODULES:
        import_optional(f"app.{name}.models")
        routes = import_optional(f"app.{name}.routes")
        blueprint = getattr(routes, "bp", None)
        if blueprint is not None:
            app.register_blueprint(blueprint)

    return app
