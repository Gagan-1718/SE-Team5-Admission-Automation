"""Candidate registration and shared account session endpoints."""
import re

from flask import Blueprint, jsonify, make_response, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.extensions import db

from .auth import (
    SESSION_COOKIE,
    create_session,
    current_identity,
    delete_current_session,
    login_required,
    load_current_user,
)
from .models import User
from .security import hash_password

bp = Blueprint("accounts", __name__, url_prefix="/accounts")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE_PATTERN = re.compile(r"^\d{10}$")


@bp.before_app_request
def load_user_for_request():
    load_current_user()


def _validation_error(message):
    return jsonify(error="validation_error", message=message), 400


def _registration_values(payload):
    if not isinstance(payload, dict):
        return None, "A JSON object is required."
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    mobile = str(payload.get("mobile", "")).strip()
    password = payload.get("password")

    if not all((name, email, mobile, password)):
        return None, "Name, email, mobile and password are required."
    if len(name) > 120 or len(name) < 2:
        return None, "Name must be between 2 and 120 characters."
    if not EMAIL_PATTERN.fullmatch(email):
        return None, "Enter a valid email address."
    if not MOBILE_PATTERN.fullmatch(mobile):
        return None, "Mobile number must contain exactly 10 digits."
    if not isinstance(password, str) or len(password) < 8:
        return None, "Password must contain at least 8 characters."
    return {"name": name, "email": email, "mobile": mobile, "password": password}, None


@bp.get("/register")
def registration_page():
    return render_template("accounts/register.html")


@bp.post("/register")
def register():
    values, error = _registration_values(request.get_json(silent=True))
    if error:
        return _validation_error(error)

    user = User(
        name=values["name"],
        email=values["email"],
        mobile=values["mobile"],
        password_hash=hash_password(values["password"]),
        role="candidate",
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="duplicate_account", message="An account with that email or mobile already exists."), 409

    return jsonify(message="Registration successful.", user_id=user.id), 201


@bp.get("/me")
@login_required
def me():
    user = current_identity()
    user.update({"name": db.session.get(User, user["id"]).name})
    return jsonify(user)


@bp.get("/admin-check")
@login_required
def admin_check():
    if current_identity()["role"] != "administrator":
        return jsonify(error="forbidden", message="You do not have permission for this resource."), 403
    return jsonify(message="Administrator access granted.")

