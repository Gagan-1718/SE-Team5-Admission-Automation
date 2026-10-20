"""Who is the current candidate? Comes from the accounts module (login).

Everything else in this module calls these helpers, so the application code never
touches sessions or cookies directly.
"""
from functools import wraps
from http import HTTPStatus

from flask import abort, jsonify, redirect, request, url_for

from app.accounts.auth import current_candidate_id as _accounts_candidate_id
from app.accounts.auth import current_identity


def current_candidate_id():
    """The logged-in candidate's id, or None (anonymous visitors and administrators)."""
    return _accounts_candidate_id()


def _json_error(code, message):
    body = {"status": code, "error": HTTPStatus(code).phrase, "message": message}
    return jsonify(body), code


def candidate_required(view):
    """JSON API: 401 if not logged in, 403 if logged in but not a candidate."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_identity() is None:
            return _json_error(401, "Authentication is required.")
        if current_candidate_id() is None:
            return _json_error(403, "Only candidates can use the application.")
        return view(*args, **kwargs)

    return wrapped


def candidate_page_required(view):
    """Browser page: anonymous visitors go to the login page, administrators get 403."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_identity() is None:
            return redirect(url_for("accounts.login_page", next=request.path))
        if current_candidate_id() is None:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
