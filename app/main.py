"""Shared routes: home page and health check."""
from flask import Blueprint, jsonify, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db

bp = Blueprint("main", __name__)


@bp.app_errorhandler(403)
def forbidden(_error):
    return render_template("403.html"), 403


@bp.app_errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@bp.app_errorhandler(500)
def server_error(_error):
    return render_template("500.html"), 500


@bp.get("/")
def home():
    return render_template("home.html")


@bp.get("/health")
def health():
    """Lightweight check used for demo-time monitoring (SAD A-21)."""
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return jsonify(status="error", database="unavailable"), 503
    return jsonify(status="ok", database="ok")
