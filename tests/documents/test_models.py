import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.documents.models import Document


def test_document_is_saved_with_pending_status(app):
    document = Document(
        candidate_id=1,
        application_id=1,
        document_type="Marksheet",
        stored_name="fictional-marksheet.pdf",
    )

    db.session.add(document)
    db.session.commit()
    document_id = document.id
    db.session.expire_all()

    saved = db.session.get(Document, document_id)

    assert saved.candidate_id == 1
    assert saved.application_id == 1
    assert saved.document_type == "Marksheet"
    assert saved.stored_name == "fictional-marksheet.pdf"
    assert saved.status == "Pending"
    assert saved.rejection_reason is None


def test_invalid_document_status_is_rejected(app):
    document = Document(
        candidate_id=1,
        application_id=1,
        document_type="Marksheet",
        stored_name="fictional-invalid-status.pdf",
        status="Unknown",
    )

    db.session.add(document)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()

def test_both_document_foreign_keys_exist(app):
    from sqlalchemy import inspect
    links = {
        (tuple(fk["constrained_columns"]), fk["referred_table"],
         tuple(fk["referred_columns"]))
        for fk in inspect(db.engine).get_foreign_keys("documents")
    }
    assert (("candidate_id",), "users", ("id",)) in links
    assert (("application_id",), "applications", ("id",)) in links


@pytest.mark.parametrize("candidate_id,application_id", [(999, 1), (1, 999)])
def test_document_cannot_reference_missing_parent(app, candidate_id, application_id):
    db.session.add(Document(candidate_id=candidate_id, application_id=application_id,
                            document_type="Marksheet", stored_name="orphan.pdf"))
    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        db.session.commit()
    db.session.rollback()
    assert db.session.execute(db.select(db.func.count(Document.id))).scalar_one() == 0


@pytest.mark.parametrize("parent", ["user", "application"])
def test_referenced_parent_cannot_be_deleted(app, parent):
    from app.accounts.models import User
    from app.application.models import Application
    db.session.add(Document(candidate_id=1, application_id=1,
                            document_type="Marksheet", stored_name="keep.pdf"))
    db.session.commit()
    model = User if parent == "user" else Application
    with pytest.raises(IntegrityError, match="FOREIGN KEY"):
        db.session.execute(db.delete(model).where(model.id == 1))
        db.session.commit()
    db.session.rollback()
    assert db.session.execute(db.select(Document)).scalar_one().stored_name == "keep.pdf"
