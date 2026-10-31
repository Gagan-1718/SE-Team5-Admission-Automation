"""The pure allotment algorithm (issue #5 ADM-F-015, issue #6 ADM-F-016).

The first test is the Test Plan's own oracle (Appendix B). If it fails, the engine is wrong,
not the test: never edit the expected values to make it pass.
"""
import random
from collections import Counter

import pytest

from app.allotment.engine import allot
from app.allotment.models import ALLOCATED, NOT_ALLOCATED

A_CSE, A_ISE, B_ECE = 101, 102, 201


def candidate(candidate_id, rank, branch_ids, category="General", reference=None, **extra):
    return {
        "candidate_id": candidate_id,
        "rank": rank,
        "reference": reference or f"ADM-2026-{candidate_id:06d}",
        "category": category,
        "branch_ids": list(branch_ids),
        **extra,
    }


def by_candidate(results):
    return {r["candidate_id"]: r for r in results}


def seats_left(seats, results):
    used = Counter((r["branch_id"], r["category"]) for r in results if r["status"] == ALLOCATED)
    return {key: free - used[key] for key, free in seats.items()}


# ------------------------------------------------------------- Appendix B oracle
ORACLE_SEATS = {(A_CSE, "General"): 2, (A_ISE, "General"): 1, (B_ECE, "General"): 1}
ORACLE_CANDIDATES = [
    candidate(1, 1, [A_CSE, A_ISE]),
    candidate(2, 2, [A_CSE, B_ECE]),
    candidate(3, 3, [A_CSE, A_ISE]),
    candidate(4, 4, [A_CSE, A_ISE]),
    candidate(5, 5, [A_CSE]),
]


def test_appendix_b_oracle_results():
    results = by_candidate(allot(ORACLE_CANDIDATES, ORACLE_SEATS))
    expected = {
        1: (ALLOCATED, A_CSE, 1),       # first choice free
        2: (ALLOCATED, A_CSE, 1),       # last A-CSE seat
        3: (ALLOCATED, A_ISE, 2),       # A-CSE full, second choice
        4: (NOT_ALLOCATED, None, None),  # A-CSE and A-ISE both full
        5: (NOT_ALLOCATED, None, None),  # only choice full
    }
    for candidate_id, (status, branch_id, priority) in expected.items():
        r = results[candidate_id]
        assert (r["status"], r["branch_id"], r["choice_priority"]) == (status, branch_id, priority), candidate_id


def test_appendix_b_oracle_seats_after_the_run():
    results = allot(ORACLE_CANDIDATES, ORACLE_SEATS)
    assert seats_left(ORACLE_SEATS, results) == {
        (A_CSE, "General"): 0,
        (A_ISE, "General"): 0,
        (B_ECE, "General"): 1,  # unchanged
    }


# ------------------------------------------- Appendix B extension (TC-015 step 3)
def test_category_rows_are_separate_no_cross_category_fallback():
    """SAD A-11: only the candidate's own category row is used."""
    seats = {(A_CSE, "General"): 1, (A_CSE, "OBC"): 1}
    results = by_candidate(allot([
        candidate(1, 1, [A_CSE]),                     # General, takes the General seat
        candidate(2, 2, [A_CSE]),                     # General, General full; must NOT take OBC
        candidate(3, 3, [A_CSE], category="OBC"),     # OBC seat is still free for an OBC candidate
    ], seats))
    assert results[1]["status"] == ALLOCATED
    assert results[2]["status"] == NOT_ALLOCATED
    assert results[3]["status"] == ALLOCATED and results[3]["category"] == "OBC"


def test_a_branch_with_no_row_for_the_category_is_skipped():
    seats = {(A_CSE, "General"): 5}
    result = allot([candidate(1, 1, [A_CSE, A_ISE], category="ST")], seats)[0]
    assert result["status"] == NOT_ALLOCATED


def test_an_ineligible_candidate_is_ignored_and_does_not_use_a_seat():
    seats = {(A_CSE, "General"): 1}
    results = allot([
        candidate(1, 1, [A_CSE], eligible=False),  # best rank, but Not Eligible at run time
        candidate(2, 2, [A_CSE]),
    ], seats)
    assert [r["candidate_id"] for r in results] == [2]  # no result row at all for candidate 1
    assert results[0]["status"] == ALLOCATED


# ------------------------------------------------------------- ordering rules
def test_candidates_are_processed_in_ascending_rank_whatever_the_input_order():
    seats = {(A_CSE, "General"): 1}
    results = by_candidate(allot([candidate(9, 50, [A_CSE]), candidate(8, 7, [A_CSE])], seats))
    assert results[8]["status"] == ALLOCATED
    assert results[9]["status"] == NOT_ALLOCATED


def test_rank_ties_are_broken_by_reference_number():
    """SAD A-10."""
    seats = {(A_CSE, "General"): 1}
    results = by_candidate(allot([
        candidate(1, 100, [A_CSE], reference="ADM-2026-000020"),
        candidate(2, 100, [A_CSE], reference="ADM-2026-000003"),
    ], seats))
    assert results[2]["status"] == ALLOCATED
    assert results[1]["status"] == NOT_ALLOCATED


def test_preferences_are_tried_in_saved_order():
    seats = {(A_CSE, "General"): 1, (A_ISE, "General"): 1}
    result = allot([candidate(1, 1, [A_ISE, A_CSE])], seats)[0]
    assert (result["branch_id"], result["choice_priority"]) == (A_ISE, 1)


def test_results_come_back_in_processing_order_with_the_data_to_save():
    results = allot(ORACLE_CANDIDATES[::-1], ORACLE_SEATS)
    assert [r["candidate_id"] for r in results] == [1, 2, 3, 4, 5]
    assert set(results[0]) == {"candidate_id", "rank", "reference", "category", "status",
                               "branch_id", "choice_priority"}


# ------------------------------------------------------------- edge cases
def test_empty_inputs_give_no_results():
    assert allot([], {}) == []


def test_an_empty_choice_list_is_not_allocated():
    assert allot([candidate(1, 1, [])], {(A_CSE, "General"): 1})[0]["status"] == NOT_ALLOCATED


def test_inputs_are_not_changed():
    seats = dict(ORACLE_SEATS)
    candidates = [dict(c, branch_ids=list(c["branch_ids"])) for c in ORACLE_CANDIDATES]
    allot(candidates, seats)
    assert seats == ORACLE_SEATS
    assert candidates == ORACLE_CANDIDATES


def test_the_same_candidate_twice_is_refused():
    with pytest.raises(ValueError):
        allot([candidate(1, 1, [A_CSE]), candidate(1, 2, [A_ISE])], ORACLE_SEATS)


def test_negative_seat_counts_are_refused():
    with pytest.raises(ValueError):
        allot([candidate(1, 1, [A_CSE])], {(A_CSE, "General"): -1})


# ------------------------------------------------------- properties on random data
@pytest.mark.parametrize("seed", range(20))
def test_random_datasets_never_overfill_and_are_deterministic(seed):
    rng = random.Random(seed)
    categories = ["General", "OBC", "SC", "ST", "EWS"]
    branches = list(range(1, 9))
    seats = {(b, c): rng.randint(0, 4) for b in branches for c in categories}
    candidates = [
        candidate(i, rng.randint(1, 500), rng.sample(branches, rng.randint(0, 5)),
                  category=rng.choice(categories), eligible=rng.random() > 0.1)
        for i in range(1, 121)
    ]

    results = allot(candidates, seats)

    # ADM-NFR-003: no category row ever goes below zero
    assert all(left >= 0 for left in seats_left(seats, results).values())
    # each eligible candidate exactly once, ineligible never
    eligible_ids = {c["candidate_id"] for c in candidates if c["eligible"]}
    assert Counter(r["candidate_id"] for r in results) == Counter(eligible_ids)
    # an allocation is always one of the candidate's own choices, in their category
    by_id = {c["candidate_id"]: c for c in candidates}
    for r in results:
        if r["status"] == ALLOCATED:
            c = by_id[r["candidate_id"]]
            assert c["branch_ids"][r["choice_priority"] - 1] == r["branch_id"]
            assert r["category"] == c["category"]
    # shuffling the input never changes the outcome
    shuffled = candidates[:]
    rng.shuffle(shuffled)
    assert allot(shuffled, seats) == results


@pytest.mark.parametrize("seed", range(10))
def test_nobody_better_ranked_could_have_been_moved_up(seed):
    """Rank order is respected: if a candidate got their k-th choice (or nothing), every
    earlier choice was already full when their turn came, so no worse-ranked candidate in
    the same category holds a seat in one of those earlier branches."""
    rng = random.Random(1000 + seed)
    branches = list(range(1, 6))
    seats = {(b, "General"): rng.randint(0, 3) for b in branches}
    candidates = [candidate(i, i, rng.sample(branches, 3)) for i in range(1, 41)]
    results = by_candidate(allot(candidates, seats))
    for c in candidates:
        mine = results[c["candidate_id"]]
        tried = c["branch_ids"] if mine["status"] == NOT_ALLOCATED else c["branch_ids"][: mine["choice_priority"] - 1]
        for branch_id in tried:
            holders = [r for r in results.values() if r["status"] == ALLOCATED and r["branch_id"] == branch_id]
            assert all(r["rank"] < c["rank"] for r in holders), (c["candidate_id"], branch_id)
