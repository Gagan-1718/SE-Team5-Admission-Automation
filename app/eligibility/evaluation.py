"""Pure eligibility decision. No database, no Flask: easy to test (SAD A-08)."""

PENDING = "Pending"
ELIGIBLE = "Eligible"
NOT_ELIGIBLE = "Not Eligible"


def evaluate_eligibility(rank, category, documents_approved, rules):
    """Return {'status': ..., 'reason': ...}.

    `rules` is any iterable of objects with `category`, `max_rank` and `active`.
    Decision order:
      1. documents not all approved       -> Pending
      2. no active rule for the category  -> Not Eligible
      3. rank above the cut-off           -> Not Eligible
      4. otherwise (rank == cut-off too)  -> Eligible
    """
    if not documents_approved:
        return {"status": PENDING, "reason": "Required documents are not all approved yet."}

    rule = next((r for r in rules if r.active and r.category == category), None)
    if rule is None:
        return {
            "status": NOT_ELIGIBLE,
            "reason": f"No active eligibility rule exists for the category '{category}'.",
        }

    if rank > rule.max_rank:
        return {
            "status": NOT_ELIGIBLE,
            "reason": f"Rank {rank} is above the {category} cut-off of {rule.max_rank}.",
        }

    return {
        "status": ELIGIBLE,
        "reason": f"Rank {rank} is within the {category} cut-off of {rule.max_rank}.",
    }
