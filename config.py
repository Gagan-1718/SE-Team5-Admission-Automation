"""Shared configuration for the Team 5 Flask application.

Nothing secret is stored in this file. Local values come from environment
variables or from the git-ignored ``instance/`` folder.
"""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

DEFAULT_DATABASE_URI = "sqlite:///" + (INSTANCE_DIR / "team5_admission.db").as_posix()


class Config:
    # Each developer gets their own local SQLite file; override with DATABASE_URL.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Set SECRET_KEY in the environment to choose your own. If it is missing,
    # create_app() creates a random key in instance/secret_key.txt (not in Git).
    SECRET_KEY = os.environ.get("SECRET_KEY")


def load_or_create_secret_key(instance_path):
    """Return a stable random key stored under the git-ignored instance folder."""
    key_file = Path(instance_path) / "secret_key.txt"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    key = secrets.token_hex(32)
    key_file.write_text(key, encoding="utf-8")
    return key
