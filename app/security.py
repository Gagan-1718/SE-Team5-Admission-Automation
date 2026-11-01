"""Shared CSRF protection and response security headers."""
import secrets

from flask import current_app, jsonify, request, session

CSRF_SESSION_KEY = "_csrf_token"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def csrf_protection_enabled():
    """Production defaults on; tests can explicitly enable real CSRF checks."""
    return current_app.config.get("CSRF_ENABLED", not current_app.testing)


def csrf_token():
    """Return a random token tied to this browser session, including before login."""
    token = session.get(CSRF_SESSION_KEY)
    if not isinstance(token, str) or not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def register_security(app):
    @app.context_processor
    def csrf_helpers():
        # Documents already pass a string named csrf_token. The distinct alias
        # keeps the base template's meta tag callable on those pages too.
        return {"csrf_token": csrf_token, "get_csrf_token": csrf_token}

    @app.before_request
    def check_csrf():
        if not csrf_protection_enabled() or request.method not in UNSAFE_METHODS:
            return None
        expected = session.get(CSRF_SESSION_KEY)
        supplied = request.headers.get("X-CSRF-Token")
        if supplied is None and not request.is_json:
            supplied = request.form.get("csrf_token")
        if (not isinstance(expected, str) or not expected
                or not isinstance(supplied, str) or not supplied
                or not secrets.compare_digest(expected.encode("utf-8"), supplied.encode("utf-8"))):
            return jsonify(
                error="csrf_failed",
                message="Invalid or missing CSRF token. Reload the page and try again.",
            ), 400
        return None

    @app.after_request
    def add_security_headers(response):
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        if CSRF_SESSION_KEY in session and response.mimetype == "text/html":
            response.headers.setdefault("Cache-Control", "no-store")
        return response
