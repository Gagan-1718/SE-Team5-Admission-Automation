"""The allotment algorithm as a pure function: no database, no Flask, no clock (issue #5)."""


def allot(candidates, seats):
    """Allot seats and return one result per candidate who took part.

    candidates: [{candidate_id, rank, reference, category, branch_ids: [...]}]  (locked order)
    seats:      {(branch_id, category): seats_free}

    CONTRACT STUB: Gagan writes the body (SAD 4.1 algorithm, test plan Appendix B oracle).
    """
    raise NotImplementedError("Contract stub: implement in issue #5.")
