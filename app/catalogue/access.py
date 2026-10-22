"""Protect catalogue administration with the shared Accounts session and role check."""
from app.accounts.auth import role_required

admin_required = role_required("administrator")
