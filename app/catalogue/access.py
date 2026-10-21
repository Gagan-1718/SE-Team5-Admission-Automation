
"""Admin-only access guard for the catalogue's administrator pages.

The admin guard is supplied through app.config["CATALOGUE_ADMIN_GUARD"].
Until a valid guard is configured and explicitly approves access, requests
are denied by default.
"""
from functools import wraps

from flask import abort, current_app


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        guard = current_app.config.get("CATALOGUE_ADMIN_GUARD")

        if not callable(guard):
            abort(403)

        if not guard():
            abort(403)

        return view(*args, **kwargs)

    return wrapped
