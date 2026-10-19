"""Who is the current candidate? TEMPORARY until login is integrated.

Varun's accounts module (#17, #19) will provide the logged-in candidate ID.
When it is merged, change ONLY this function to read that value and return 401
for anonymous visitors. Everything else in this module calls this function.
"""

TEMPORARY_CANDIDATE_ID = 1


def current_candidate_id():
    return TEMPORARY_CANDIDATE_ID
