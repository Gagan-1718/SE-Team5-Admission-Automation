"""Explicit, transactional SQLite upgrade for existing document metadata.

Never runs automatically. Upload files are untouched. Orphaned references or
unexpected schema objects stop the upgrade rather than discarding local data.
"""
import click
from sqlalchemy import MetaData, inspect
from sqlalchemy.schema import CreateIndex, CreateTable

from app.documents.models import Document
from app.extensions import db


def upgrade_document_foreign_keys():
    """Add document foreign keys, preserving rows, ids, indexes and file names."""
    if db.engine.dialect.name != "sqlite":
        raise ValueError("This upgrade supports SQLite only.")
    db.session.remove()
    with db.engine.connect() as connection:
        # SQLite needs an explicit transaction so CREATE/DROP/RENAME roll back too.
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            inspector = inspect(connection)
            if not inspector.has_table("documents"):
                raise ValueError("Run init-db before upgrading document references.")
            expected = {
                (("candidate_id",), "users", ("id",)),
                (("application_id",), "applications", ("id",)),
            }
            links = {
                (tuple(fk["constrained_columns"]), fk["referred_table"],
                 tuple(fk["referred_columns"]))
                for fk in inspector.get_foreign_keys("documents")
            }
            orphan_ids = connection.exec_driver_sql(
                "SELECT d.id FROM documents AS d "
                "LEFT JOIN users AS u ON u.id = d.candidate_id "
                "LEFT JOIN applications AS a ON a.id = d.application_id "
                "WHERE u.id IS NULL OR a.id IS NULL ORDER BY d.id"
            ).scalars().all()
            if orphan_ids:
                raise ValueError(
                    f"Upgrade stopped: orphaned document IDs {orphan_ids}. "
                    "Repair their candidate/application references and retry; no rows were deleted."
                )
            if expected.issubset(links):
                connection.commit()
                return False

            columns = [column.name for column in Document.__table__.columns]
            if set(columns) != {c["name"] for c in inspector.get_columns("documents")}:
                raise ValueError("Unexpected document columns; upgrade manually without losing data.")
            # Refuse to silently remove custom objects or cascade incoming references.
            triggers = connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'documents'"
            ).all()
            if triggers or inspector.has_table("documents_fk_upgrade"):
                raise ValueError("Unexpected document triggers or upgrade table; inspect before retrying.")
            known_indexes = {index.name for index in Document.__table__.indexes}
            if any(index["name"] not in known_indexes
                   for index in inspector.get_indexes("documents")):
                raise ValueError("Custom document indexes found; upgrade manually to preserve them.")
            for table in inspector.get_table_names():
                if any(fk["referred_table"] == "documents"
                       for fk in inspector.get_foreign_keys(table)):
                    raise ValueError("Incoming document foreign keys found; upgrade manually.")

            metadata = MetaData()
            for name in ("users", "applications"):
                db.metadata.tables[name].to_metadata(metadata)
            replacement = Document.__table__.to_metadata(metadata, name="documents_fk_upgrade")
            connection.execute(CreateTable(replacement))
            quoted_columns = ", ".join(f'"{name}"' for name in columns)
            connection.exec_driver_sql(
                f"INSERT INTO documents_fk_upgrade ({quoted_columns}) "
                f"SELECT {quoted_columns} FROM documents"
            )
            connection.exec_driver_sql("DROP TABLE documents")
            connection.exec_driver_sql("ALTER TABLE documents_fk_upgrade RENAME TO documents")
            for index in Document.__table__.indexes:
                connection.execute(CreateIndex(index))
            if connection.exec_driver_sql("PRAGMA foreign_key_check(documents)").all():
                raise ValueError("Foreign-key validation failed; upgrade rolled back.")
            connection.commit()
            return True
        except Exception:
            connection.rollback()
            raise


def register_commands(app):
    @app.cli.command("upgrade-document-references")
    def upgrade_document_references():
        """Add document foreign keys to an existing SQLite database without resetting it."""
        try:
            changed = upgrade_document_foreign_keys()
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo("Document foreign keys added; metadata preserved."
                   if changed else "Document foreign keys are already present.")
