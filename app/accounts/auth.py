"""Session and authorization helpers shared by account routes and modules."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import g, jsonify, redirect, request, url_for

from app.extensions import db

from .models import User, UserSession

SESSION_COOKIE = "team5_session"
SESSION_TTL = timedelta(hours=8)


def _token_hash(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def load_current_user():
    """Load the authenticated user from a hashed server-side session token."""
    g.current_user = None
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        return

    session = db.session.get(UserSession, _token_hash(raw_token))
    if not session:
        return
    if session.is_expired():
        db.session.delete(session)
        db.session.commit()
        return
    g.current_user = session.user


def create_session(user):
    raw_token = secrets.token_urlsafe(32)
    session = UserSession(
        token_hash=_token_hash(raw_token),
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + SESSION_TTL,
    )
    db.session.add(session)
    db.session.commit()
    return raw_token


def delete_current_session():
    raw_token = request.cookies.get(SESSION_COOKIE)
    if raw_token:
        session = db.session.get(UserSession, _token_hash(raw_token))
        if session:
            db.session.delete(session)
            db.session.commit()


def current_identity():
    """Return the stable cross-module identity contract for the request."""
    return g.current_user.identity() if g.current_user else None


def current_candidate_id():
    """Return the authenticated candidate ID, never an administrator ID."""
    current_user = getattr(g, "current_user", None)
    if current_user and current_user.role == "candidate":
        return int(current_user.id)
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.current_user:
            return jsonify(error="authentication_required", message="Authentication is required."), 401
        return view(*args, **kwargs)

    return wrapped


def page_login_required(view):
    """Redirect anonymous browser-page requests to the login page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.current_user:
            return redirect(url_for("accounts.login_page", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.current_user:
                return jsonify(error="authentication_required", message="Authentication is required."), 401
            if g.current_user.role != role:
                return jsonify(error="forbidden", message="You do not have permission for this resource."), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator

