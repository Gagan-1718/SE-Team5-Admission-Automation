"""Pure decision function: no database needed."""
from types import SimpleNamespace

from app.eligibility.evaluation import evaluate_eligibility

RULES = [
    SimpleNamespace(category="General", max_rank=20000, active=True),
    SimpleNamespace(category="OBC", max_rank=30000, active=True),
    SimpleNamespace(category="EWS", max_rank=25000, active=False),
]


def test_pending_when_documents_not_approved():
    result = evaluate_eligibility(1000, "General", False, RULES)
    assert result == {"status": "Pending", "reason": "Required documents are not all approved yet."}


def test_pending_wins_even_for_unknown_category():
    assert evaluate_eligibility(1, "Nope", False, RULES)["status"] == "Pending"


def test_eligible_below_cutoff():
    result = evaluate_eligibility(1000, "General", True, RULES)
    assert result["status"] == "Eligible"
    assert result["reason"] == "Rank 1000 is within the General cut-off of 20000."


def test_not_eligible_above_cutoff():
    result = evaluate_eligibility(90000, "General", True, RULES)
    assert result["status"] == "Not Eligible"
    assert result["reason"] == "Rank 90000 is above the General cut-off of 20000."


def test_rank_equal_to_cutoff_is_eligible():
    assert evaluate_eligibility(20000, "General", True, RULES)["status"] == "Eligible"


def test_rank_one_above_cutoff_is_not_eligible():
    assert evaluate_eligibility(20001, "General", True, RULES)["status"] == "Not Eligible"


def test_unknown_category_is_not_eligible_and_names_category():
    result = evaluate_eligibility(100, "Martian", True, RULES)
    assert result["status"] == "Not Eligible"
    assert "Martian" in result["reason"]


def test_inactive_rule_is_treated_as_no_rule():
    result = evaluate_eligibility(100, "EWS", True, RULES)
    assert result["status"] == "Not Eligible"
    assert "EWS" in result["reason"]


def test_empty_rules_means_not_eligible():
    assert evaluate_eligibility(1, "General", True, [])["status"] == "Not Eligible"
