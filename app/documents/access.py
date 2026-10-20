"""Temporary admin authorization boundary until Accounts integration."""

from functools import wraps

from flask import abort, current_app


def admin_required(view):
    @wraps(view)
    def guarded(*args, **kwargs):
        guard = current_app.config.get("DOCUMENTS_ADMIN_GUARD")
        # An absent guard must never expose student documents.
        if not callable(guard) or guard() is not True:
            abort(403)
        return view(*args, **kwargs)

    return guarded
