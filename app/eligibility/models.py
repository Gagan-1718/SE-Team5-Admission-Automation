"""Database model for eligibility cut-off rules (owner: Tasya)."""
from sqlalchemy import CheckConstraint, true

from app.extensions import db

# Agreed category names. Defined here so this module never imports accounts.
CATEGORIES = ("General", "OBC", "SC", "ST", "EWS")

_category_list = ", ".join(f"'{name}'" for name in CATEGORIES)


class EligibilityRule(db.Model):
    """One cut-off rule: candidates in `category` are eligible up to `max_rank`."""

    __tablename__ = "eligibility_rules"
    __table_args__ = (
        CheckConstraint(f"category IN ({_category_list})", name="ck_eligibility_rules_category"),
        CheckConstraint("max_rank > 0", name="ck_eligibility_rules_max_rank_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False, unique=True)
    max_rank = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=true())

    def __repr__(self):
        return f"<EligibilityRule {self.category} max_rank={self.max_rank} active={self.active}>"
