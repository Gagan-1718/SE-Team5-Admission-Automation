
"""Eligibility pages and administration."""

from flask import (
    Blueprint,
    abort,
    jsonify,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select

from app.accounts.auth import (
    current_candidate_id,
    page_login_required,
    role_required,
)
from app.audit.services import record_admin_action
from app.extensions import db

from .models import CATEGORIES, EligibilityRule
from .services import ExamDetailsNotEntered, get_eligibility

bp = Blueprint("eligibility", __name__)


def _parse_max_rank(value):
    """Accept only a positive whole number."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Cut-off rank is required.")

    value = value.strip()

    if not value.isascii() or not value.isdecimal():
        raise ValueError("Cut-off rank must be a whole number.")

    rank = int(value)

    if rank <= 0:
        raise ValueError("Cut-off rank must be greater than zero.")

    return rank


def _render_admin_rules(errors=None, values=None, status=200):
    """Render the rules page with inline validation errors."""
    rules = db.session.scalars(
        select(EligibilityRule).order_by(EligibilityRule.id)
    ).all()

    rules_by_category = {rule.category: rule for rule in rules}

    return (
        render_template(
            "eligibility/admin_rules.html",
            categories=CATEGORIES,
            rules_by_category=rules_by_category,
            errors=errors or {},
            values=values or {},
        ),
        status,
    )


# Candidate routes

@bp.get("/eligibility")
@page_login_required
def eligibility_page():
    candidate_id = current_candidate_id()

    if candidate_id is None:
        abort(403)

    return render_template(
        "eligibility/status.html",
        result=get_eligibility(candidate_id),
    )


@bp.get("/api/v1/candidates/me/eligibility")
@role_required("candidate")
def eligibility_json():
    try:
        return jsonify(
            get_eligibility(
                current_candidate_id(),
                require_exam_details=True,
            )
        )
    except ExamDetailsNotEntered:
        return jsonify(
            error="exam_details_not_entered",
            message="exam details not entered",
        ), 422


# Administrator routes

@bp.get("/admin/eligibility-rules")
@role_required("administrator")
def admin_rules():
    return _render_admin_rules()


@bp.post("/admin/eligibility-rules")
@role_required("administrator")
def admin_rule_create():
    category = request.form.get("category", "").strip()
    raw_rank = request.form.get("max_rank", "")

    if category not in CATEGORIES:
        abort(400)

    try:
        max_rank = _parse_max_rank(raw_rank)
    except ValueError as exc:
        return _render_admin_rules(
            errors={category: str(exc)},
            values={category: raw_rank},
            status=422,
        )

    existing = db.session.scalar(
        select(EligibilityRule).where(
            EligibilityRule.category == category
        )
    )

    if existing is not None:
        return _render_admin_rules(
            errors={category: f"A rule for {category} already exists."},
            values={category: raw_rank},
            status=409,
        )

    rule = EligibilityRule(
        category=category,
        max_rank=max_rank,
        active=True,
    )

    try:
        db.session.add(rule)
        db.session.flush()

        record_admin_action(
            "rule.create",
            "EligibilityRule",
            rule.id,
            commit=False,
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return _render_admin_rules(status=201)


@bp.post("/admin/eligibility-rules/<int:rule_id>")
@role_required("administrator")
def admin_rule_update(rule_id):
    rule = db.get_or_404(EligibilityRule, rule_id)

    raw_rank = request.form.get("max_rank", "")

    try:
        max_rank = _parse_max_rank(raw_rank)
    except ValueError as exc:
        return _render_admin_rules(
            errors={rule.category: str(exc)},
            values={rule.category: raw_rank},
            status=422,
        )

    active = request.form.get("active") == "on"

    try:
        rule.max_rank = max_rank
        rule.active = active

        record_admin_action(
            "rule.update",
            "EligibilityRule",
            rule.id,
            commit=False,
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return _render_admin_rules()
