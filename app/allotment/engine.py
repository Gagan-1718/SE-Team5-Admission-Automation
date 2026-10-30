"""The allotment algorithm as a pure function: no database, no Flask, no clock (issue #5).

SAD 4.1, ADM-F-015 and ADM-F-016:
  1. Candidates are processed in ascending rank; ties go to the lower application
     reference number (SAD A-10). KCET and COMEDK ranks are compared as stored.
  2. Each candidate's locked choices are tried in saved order.
  3. A choice is satisfied only by a free seat in the row for that branch and the
     candidate's own category; there is no cross-category fallback (SAD A-11).
  4. The seat is taken at once, before the next candidate is processed.
  5. A candidate with no satisfiable choice is Not Allocated.
Candidates marked ``eligible: False`` (Not Eligible at run time) are skipped and get no
result at all, which is different from Not Allocated (decision D2-06).
"""
from .models import ALLOCATED, NOT_ALLOCATED


def allot(candidates, seats):
    """Allot seats and return one result per candidate who took part, in processing order.

    candidates: [{candidate_id, rank, reference, category, branch_ids: [...], eligible?}]
                ``branch_ids`` is the locked list in priority order; ``eligible`` defaults to True.
    seats:      {(branch_id, category): seats_free}

    Each result: {candidate_id, rank, reference, category, status, branch_id, choice_priority}.
    Neither argument is changed.
    """
    free = {}
    for key, count in seats.items():
        if count < 0:
            raise ValueError(f"Seat count for {key} is negative: {count}.")
        free[key] = count

    seen = set()
    for c in candidates:
        if c["candidate_id"] in seen:
            raise ValueError(f"Candidate {c['candidate_id']} appears more than once.")
        seen.add(c["candidate_id"])

    taking_part = [c for c in candidates if c.get("eligible", True)]
    taking_part.sort(key=lambda c: (c["rank"], c["reference"]))

    results = []
    for c in taking_part:
        branch_id = choice_priority = None
        for priority, wanted in enumerate(c["branch_ids"], start=1):
            key = (wanted, c["category"])
            if free.get(key, 0) > 0:
                free[key] -= 1
                branch_id, choice_priority = wanted, priority
                break
        results.append({
            "candidate_id": c["candidate_id"],
            "rank": c["rank"],
            "reference": c["reference"],
            "category": c["category"],
            "status": ALLOCATED if branch_id is not None else NOT_ALLOCATED,
            "branch_id": branch_id,
            "choice_priority": choice_priority,
        })
    return results
