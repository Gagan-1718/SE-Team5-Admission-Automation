"""Choice list services (owner: Varun).

CONTRACT STUBS: names, parameters and error types are agreed in SPRINT_TWO_START_HERE.md
section 4.3. Varun replaces the bodies (issues #21, #22, #23); do not rename anything.
Each error carries the HTTP status the routes should use.
"""


class ChoiceError(Exception):
    status_code = 400


class NotEligible(ChoiceError):
    """The candidate is not Eligible, so they cannot add choices."""
    status_code = 403


class DuplicateChoice(ChoiceError):
    """That branch is already in the candidate's list."""
    status_code = 409


class ChoicesLocked(ChoiceError):
    """The list is locked: no add, remove or reorder."""
    status_code = 409


class UnknownBranch(ChoiceError):
    """No such branch in the catalogue."""
    status_code = 404


class OrderMismatch(ChoiceError):
    """The ids sent for reordering are not exactly the candidate's current choices."""
    status_code = 400


class AlreadyLocked(ChoiceError):
    status_code = 409


class NothingToLock(ChoiceError):
    """Locking needs at least one choice."""
    status_code = 422


def _todo(issue):
    raise NotImplementedError(f"Contract stub: implement in issue {issue}.")


def list_choices(candidate_id):
    """The candidate's Choice rows ordered by priority."""
    _todo("#21")


def add_choice(candidate_id, branch_id):
    """Add a branch at the next priority. NotEligible | DuplicateChoice | ChoicesLocked | UnknownBranch."""
    _todo("#21")


def remove_choice(candidate_id, choice_id):
    """Remove a choice and renumber. ChoicesLocked."""
    _todo("#21")


def reorder(candidate_id, ordered_choice_ids):
    """Save a new order; returns the list. ChoicesLocked | OrderMismatch."""
    _todo("#22")


def lock(candidate_id):
    """Lock the list for ever. AlreadyLocked | NothingToLock."""
    _todo("#23")


def is_locked(candidate_id):
    _todo("#23")


def locked_candidate_ids():
    """Ids of every candidate who has locked their list (used by the allotment run)."""
    _todo("#23")


def get_locked_branch_ids(candidate_id):
    """Branch ids in priority order for a locked list; [] when the list is not locked."""
    _todo("#23")
