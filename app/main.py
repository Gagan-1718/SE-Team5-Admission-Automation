"""Shared routes: home page and health check."""
from flask import Blueprint, jsonify, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .extensions import db

bp = Blueprint("main", __name__)


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
