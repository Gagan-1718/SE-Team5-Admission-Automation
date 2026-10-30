"""Result publication and seat decision services (owner: Dikshith).

CONTRACT STUBS: names, parameters and error types are agreed in SPRINT_TWO_START_HERE.md
section 4.3. Dikshith replaces the bodies (issues #12, #13, #14); do not rename anything.
"""

NOT_PUBLISHED = "NOT_PUBLISHED"
NOT_IN_RUN = "NOT_IN_RUN"
NOT_ALLOCATED = "NOT_ALLOCATED"
ALLOCATED = "ALLOCATED"
VIEW_STATES = (NOT_PUBLISHED, NOT_IN_RUN, NOT_ALLOCATED, ALLOCATED)


class ResultError(Exception):
    status_code = 400


class RunNotFound(ResultError):
    status_code = 404


class AlreadyPublished(ResultError):
    status_code = 409


class NotPublished(ResultError):
    """Results are not published yet."""
    status_code = 404


class NotAllocated(ResultError):
    """The candidate has no seat to accept or reject (Not Allocated, or not in the run)."""
    status_code = 422


class AlreadyDecided(ResultError):
    status_code = 409


def _todo(issue):
    raise NotImplementedError(f"Contract stub: implement in issue {issue}.")


def publish(run_id, actor_id):
    """Publish a completed run. RunNotFound | AlreadyPublished."""
    _todo("#12")


def is_published(run_id):
    """True once the run has been published (used by the administrator dashboard banner)."""
    _todo("#12")


def candidate_view(candidate_id):
    """{state: NOT_PUBLISHED | NOT_IN_RUN | NOT_ALLOCATED | ALLOCATED, result?, decision?}."""
    _todo("#13")


def decide(candidate_id, decision):
    """Record 'Accepted' or 'Rejected' once. NotPublished | NotAllocated | AlreadyDecided."""
    _todo("#14")
