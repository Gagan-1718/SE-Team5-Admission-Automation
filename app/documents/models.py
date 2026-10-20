"""Document metadata for candidate admission applications."""

from app.extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)

    # No cross-module foreign keys until the team integrates its models.
    candidate_id = db.Column(db.Integer, nullable=False, index=True)
    application_id = db.Column(db.Integer, nullable=False, index=True)

    document_type = db.Column(db.String(80), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False, unique=True)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending",
    )
    rejection_reason = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('Pending', 'Approved', 'Rejected')",
            name="ck_documents_status",
        ),
    )