"""EligibilityRule constraints and the repeatable seed."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.eligibility.models import EligibilityRule
from app.eligibility.seed import DEFAULT_RULES, seed
from app.extensions import db


@pytest.fixture(autouse=True)
def use_app(app):
    """Run every test in this file with the shared `app` fixture (temporary DB + app context)."""


def _cutoffs():
    return {r.category: r.max_rank for r in db.session.query(EligibilityRule).all()}


def test_seed_creates_agreed_cutoffs():
    seed()
    assert _cutoffs() == {"General": 20000, "OBC": 30000, "SC": 40000, "ST": 40000, "EWS": 25000}


def test_seed_is_repeatable():
    seed()
    seed()
    assert db.session.query(EligibilityRule).count() == len(DEFAULT_RULES)


def test_seed_does_not_overwrite_an_edited_rule():
    seed()
    rule = db.session.query(EligibilityRule).filter_by(category="General").one()
    rule.max_rank = 5
    db.session.commit()
    seed()
    assert _cutoffs()["General"] == 5


def test_new_rule_is_active_by_default():
    db.session.add(EligibilityRule(category="General", max_rank=10))
    db.session.commit()
    assert db.session.query(EligibilityRule).one().active is True


@pytest.mark.parametrize(
    "category, max_rank",
    [("General", 0), ("General", -5), ("Martian", 100)],
)
def test_database_rejects_bad_rules(category, max_rank):
    db.session.add(EligibilityRule(category=category, max_rank=max_rank))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_database_rejects_duplicate_category():
    db.session.add(EligibilityRule(category="OBC", max_rank=10))
    db.session.commit()
    db.session.add(EligibilityRule(category="OBC", max_rank=20))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
