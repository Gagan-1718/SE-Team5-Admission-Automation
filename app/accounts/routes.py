"""Candidate registration and shared account session endpoints."""
import re

from flask import Blueprint, jsonify, make_response, render_template, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db

from .auth import (
    SESSION_COOKIE,
    create_session,
    current_identity,
    delete_current_session,
    login_required,
    load_current_user,
    role_required,
)
from .models import User
from .security import hash_password, verify_password

bp = Blueprint("accounts", __name__, url_prefix="/accounts")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE_PATTERN = re.compile(r"^\d{10}$")
PROFILE_CATEGORIES = {"General", "OBC", "SC", "ST"}


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


@bp.get("/login")
def login_page():
    return render_template("accounts/login.html")


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


@bp.post("/login")
def login():
    payload = request.get_json(silent=True)
    identifier = str(payload.get("identifier", "")).strip() if isinstance(payload, dict) else ""
    password = payload.get("password") if isinstance(payload, dict) else None
    user = db.session.execute(
        db.select(User).where((User.email == identifier.lower()) | (User.mobile == identifier))
    ).scalar_one_or_none()
    if not user or not verify_password(user.password_hash, password):
        return jsonify(error="invalid_credentials", message="Invalid credentials."), 401

    response = make_response(
        jsonify(message="Login successful.", user_id=user.id, role=user.role)
    )
    response.set_cookie(
        SESSION_COOKIE,
        create_session(user),
        httponly=True,
        samesite="Lax",
        secure=request.is_secure,
        max_age=8 * 60 * 60,
    )
    return response


@bp.post("/logout")
@login_required
def logout():
    delete_current_session()
    response = make_response("", 204)
    response.delete_cookie(SESSION_COOKIE)
    return response


@bp.get("/me")
@login_required
def me():
    user = current_identity()
    user.update({"name": db.session.get(User, user["id"]).name})
    return jsonify(user)


@bp.get("/admin-check")
@role_required("administrator")
def admin_check():
    return jsonify(message="Administrator access granted.")


@bp.get("/dashboard")
@login_required
def dashboard():
    return jsonify(message="Candidate dashboard", identity=current_identity())


@bp.get("/profile")
@login_required
def profile():
    user = db.session.get(User, current_identity()["id"])
    return jsonify(
        id=user.id,
        name=user.name,
        email=user.email,
        mobile=user.mobile,
        role=user.role,
        rank=user.rank,
        category=user.category,
    )


@bp.get("/profile-page")
@login_required
def profile_page():
    return render_template("accounts/profile.html")


@bp.put("/profile")
@login_required
def update_profile():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _validation_error("A JSON object is required.")

    name = str(payload.get("name", "")).strip()
    mobile = str(payload.get("mobile", "")).strip()
    category = str(payload.get("category", "")).strip()
    try:
        rank = int(payload.get("rank"))
    except (TypeError, ValueError):
        return _validation_error("Rank must be a positive integer.")

    if not 2 <= len(name) <= 120:
        return _validation_error("Name must be between 2 and 120 characters.")
    if not MOBILE_PATTERN.fullmatch(mobile):
        return _validation_error("Mobile number must contain exactly 10 digits.")
    if rank < 1:
        return _validation_error("Rank must be a positive integer.")
    if category not in PROFILE_CATEGORIES:
        return _validation_error("Category must be General, OBC, SC or ST.")

    user = db.session.get(User, current_identity()["id"])
    user.name, user.mobile, user.rank, user.category = name, mobile, rank, category
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="duplicate_account", message="That mobile number is already registered."), 409
    return jsonify(message="Profile updated successfully.")

