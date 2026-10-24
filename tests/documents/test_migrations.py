"""Existing SQLite databases upgrade without losing metadata or upload files."""
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.documents.models import Document
from app.documents.migrations import upgrade_document_foreign_keys
from app.extensions import db


@pytest.fixture
def legacy_table(app, tmp_path):
    db.session.remove()
    with db.engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE documents")
        connection.exec_driver_sql("""
            CREATE TABLE documents (
                id INTEGER NOT NULL PRIMARY KEY,
                candidate_id INTEGER NOT NULL,
                application_id INTEGER NOT NULL,
                document_type VARCHAR(80) NOT NULL,
                stored_name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(20) NOT NULL,
                rejection_reason TEXT,
                CONSTRAINT ck_documents_status CHECK (status IN ('Pending', 'Approved', 'Rejected'))
            )
        """)
        connection.exec_driver_sql("CREATE INDEX ix_documents_candidate_id ON documents (candidate_id)")
        connection.exec_driver_sql("CREATE INDEX ix_documents_application_id ON documents (application_id)")
    upload = tmp_path / "existing.pdf"
    upload.write_bytes(b"fictional existing upload")
    return upload


def legacy_row(candidate_id=1):
    with db.engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO documents VALUES (42, ?, 1, 'Marksheet', 'existing.pdf', 'Rejected', 'Unreadable')",
            (candidate_id,),
        )


def test_upgrade_preserves_metadata_and_files(app, legacy_table):
    legacy_row()
    assert upgrade_document_foreign_keys() is True
    document = db.session.get(Document, 42)
    assert (document.candidate_id, document.application_id, document.document_type,
            document.stored_name, document.status, document.rejection_reason) == (
                1, 1, "Marksheet", "existing.pdf", "Rejected", "Unreadable")
    assert legacy_table.read_bytes() == b"fictional existing upload"
    inspector = inspect(db.engine)
    assert {fk["referred_table"] for fk in inspector.get_foreign_keys("documents")} == {"users", "applications"}
    assert {index["name"] for index in inspector.get_indexes("documents")} == {
        "ix_documents_candidate_id", "ix_documents_application_id"}
    db.session.remove()
    assert upgrade_document_foreign_keys() is False
    assert db.session.get(Document, 42).rejection_reason == "Unreadable"


def test_upgraded_database_enforces_foreign_keys(app, legacy_table):
    assert upgrade_document_foreign_keys() is True
    db.session.add(Document(candidate_id=999, application_id=1, document_type="Marksheet",
                            stored_name="bad.pdf"))
    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        db.session.commit()
    db.session.rollback()


def test_orphaned_legacy_rows_stop_upgrade_without_data_loss(app, legacy_table):
    legacy_row(candidate_id=999)
    result = app.test_cli_runner().invoke(args=["upgrade-document-references"])
    assert result.exit_code == 1
    assert "orphaned document IDs [42]" in result.output
    assert inspect(db.engine).get_foreign_keys("documents") == []
    assert db.session.get(Document, 42).candidate_id == 999
    assert legacy_table.exists()
    assert not inspect(db.engine).has_table("documents_fk_upgrade")


def test_upgrade_cli_is_safe_to_repeat_on_new_database(app):
    for _ in range(2):
        result = app.test_cli_runner().invoke(args=["upgrade-document-references"])
        assert result.exit_code == 0, result.output
        assert "already present" in result.output


def test_upgrade_failure_rolls_back_original_table(app, legacy_table, monkeypatch):
    import app.documents.migrations as migrations
    legacy_row()

    def fail_index(*args, **kwargs):
        raise RuntimeError("Simulated index failure")

    monkeypatch.setattr(migrations, "CreateIndex", fail_index)
    with pytest.raises(RuntimeError, match="Simulated index failure"):
        upgrade_document_foreign_keys()
    assert inspect(db.engine).get_foreign_keys("documents") == []
    assert db.session.get(Document, 42).rejection_reason == "Unreadable"
    assert not inspect(db.engine).has_table("documents_fk_upgrade")
    assert legacy_table.exists()
