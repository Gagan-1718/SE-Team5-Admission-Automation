"""Admin-only access guard for the catalogue's administrator pages.

Uses the shared Accounts role check, the same one the documents module uses:
anonymous visitors get 401, signed-in candidates get 403, administrators pass.
"""
from app.accounts.auth import role_required

admin_required = role_required("administrator")
