"""Candidate registration and shared account session endpoints."""
import re
from datetime import date

from flask import Blueprint, jsonify, make_response, render_template, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db

from .auth import (
    SESSION_COOKIE,
    create_session,
    current_identity,
    current_candidate_id,
    delete_current_session,
    login_required,
    load_current_user,
    page_login_required,
    role_required,
)
from .constants import ALLOWED_CATEGORIES, EXAM_TYPES
from .models import ExamRecord, User
from .services import get_exam_details
from .security import hash_password, verify_password

bp = Blueprint("accounts", __name__, url_prefix="/accounts")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE_PATTERN = re.compile(r"^\d{10}$")
PINCODE_PATTERN = re.compile(r"^\d{6}$")
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
    date_of_birth = _parse_date_of_birth(payload.get("date_of_birth"))
    password = payload.get("password")

    if not all((name, email, mobile, password, date_of_birth)):
        return None, "Name, email, mobile, date of birth and password are required."
    if len(name) > 120 or len(name) < 2:
        return None, "Name must be between 2 and 120 characters."
    if not EMAIL_PATTERN.fullmatch(email):
        return None, "Enter a valid email address."
    if not MOBILE_PATTERN.fullmatch(mobile):
        return None, "Mobile number must contain exactly 10 digits."
    if not isinstance(password, str) or len(password) < 8:
        return None, "Password must contain at least 8 characters."
    if date_of_birth is None:
        return None, "Enter a valid date of birth in the past."
    return {"name": name, "email": email, "mobile": mobile, "password": password, "date_of_birth": date_of_birth}, None


def _parse_date_of_birth(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed < date.today() else None


@bp.get("/register")
def registration_page():
    return render_template("accounts/register.html", today=date.today().isoformat())


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
        date_of_birth=values["date_of_birth"],
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
        date_of_birth=user.date_of_birth.isoformat() if user.date_of_birth else None,
        address_line=user.address_line,
        city=user.city,
        pincode=user.pincode,
        role=user.role,
        rank=user.rank,
        category=user.category,
    )


@bp.get("/profile-page")
@page_login_required
def profile_page():
    from app.application.services import get_submitted_application

    return render_template(
        "accounts/profile.html",
        exam_types=EXAM_TYPES,
        categories=ALLOWED_CATEGORIES,
        exam_locked=get_submitted_application(current_candidate_id()) is not None,
    )


@bp.put("/profile")
@login_required
def update_profile():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _validation_error("A JSON object is required.")
    if any(field in payload for field in ("exam_type", "rank", "category", "score")):
        return _validation_error("Exam details must be submitted through /accounts/exam-details.")

    name = str(payload.get("name", "")).strip()
    mobile = str(payload.get("mobile", "")).strip()
    address_line = str(payload.get("address_line", "")).strip() or None
    city = str(payload.get("city", "")).strip() or None
    pincode = str(payload.get("pincode", "")).strip() or None

    if not 2 <= len(name) <= 120:
        return _validation_error("Name must be between 2 and 120 characters.")
    if not MOBILE_PATTERN.fullmatch(mobile):
        return _validation_error("Mobile number must contain exactly 10 digits.")
    if pincode is not None and not PINCODE_PATTERN.fullmatch(pincode):
        return _validation_error("Pincode must contain exactly 6 digits.")

    user = db.session.get(User, current_identity()["id"])
    user.name, user.mobile = name, mobile
    user.address_line, user.city, user.pincode = address_line, city, pincode
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="duplicate_account", message="That mobile number is already registered."), 409
    return jsonify(message="Profile updated successfully.")


@bp.put("/exam-details")
@role_required("candidate")
def update_exam_details():
    from app.application.services import get_submitted_application

    if get_submitted_application(current_candidate_id()) is not None:
        return jsonify(
            error="exam_details_locked",
            message="Exam details are locked after you submit your application",
        ), 409
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _validation_error("A JSON object is required.")

    exam_type = payload.get("exam_type")
    category = payload.get("category")
    try:
        rank = int(payload.get("rank"))
        score = float(payload.get("score"))
    except (TypeError, ValueError):
        return jsonify(error="no_matching_record", message="No matching exam record was found."), 422

    if exam_type not in EXAM_TYPES or category not in ALLOWED_CATEGORIES:
        return jsonify(error="no_matching_record", message="No matching exam record was found."), 422

    record = db.session.execute(
        db.select(ExamRecord).where(
            ExamRecord.exam_type == exam_type,
            ExamRecord.rank == rank,
            ExamRecord.category == category,
            ExamRecord.score == score,
        )
    ).scalar_one_or_none()
    if record is None:
        return jsonify(error="no_matching_record", message="No matching exam record was found."), 422

    user = db.session.get(User, current_candidate_id())
    user.exam_record_id = record.id
    user.rank = record.rank
    user.category = record.category
    db.session.commit()
    return jsonify(message="Exam details saved successfully.", exam_details=get_exam_details(user.id))

