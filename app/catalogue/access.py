"""Admin-only access guard for the catalogue's administrator pages.

The accounts module (login, roles) is owned by someone else and is not in the shared
foundation yet, so this module must not import it. Instead the admin routes call a guard
supplied through ``app.config["CATALOGUE_ADMIN_GUARD"]``: a function that returns True
for an administrator. When accounts lands, set that key (or change the two lines below)
to call its role check. Until a guard is configured the pages are OPEN - fine for local
development only, not for the acceptance demo.
"""
from functools import wraps

from flask import abort, current_app


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        guard = current_app.config.get("CATALOGUE_ADMIN_GUARD")
        if guard is not None and not guard():
            abort(403)
        return view(*args, **kwargs)

    return wrapped
