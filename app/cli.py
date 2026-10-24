"""Database commands: ``flask --app app init-db`` and ``flask --app app seed-db``."""
import click

from . import MODULES, import_optional
from .extensions import db
from .setup_check import seed as seed_setup_check


def register_commands(app):
    from .documents.migrations import register_commands as register_document_commands

    register_document_commands(app)

    @app.cli.command("init-db")
    @click.option("--reset", is_flag=True, help="Drop all tables first (local development data is lost).")
    def init_db(reset):
        """Create all database tables (safe to run repeatedly)."""
        if reset:
            db.drop_all()
            click.echo("Dropped all tables.")
        db.create_all()
        click.echo("Database tables are ready.")

    @app.cli.command("seed-db")
    def seed_db():
        """Insert fictional seed data (safe to run repeatedly)."""
        db.create_all()
        seed_setup_check()
        for name in MODULES:
            module_seed = import_optional(f"app.{name}.seed")
            if module_seed is not None:
                module_seed.seed()
                click.echo(f"Seeded {name}.")
        click.echo("Fictional seed data is ready.")
