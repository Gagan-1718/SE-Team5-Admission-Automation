"""Shared password hashing helpers for the Accounts module.

The rest of the application must call these helpers instead of comparing or
storing passwords directly. Werkzeug's password-hashing implementation adds a
unique salt and stores the algorithm parameters with the resulting hash.
"""
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Return a salted one-way hash; never return or log the input password."""
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash: str, password: str) -> bool:
    """Safely verify a submitted password against a stored hash."""
    if not isinstance(password_hash, str) or not isinstance(password, str):
        return False
    try:
        return check_password_hash(password_hash, password)
    except (ValueError, TypeError):
        return False

