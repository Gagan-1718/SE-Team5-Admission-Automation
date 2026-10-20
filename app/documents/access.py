"""Document administration uses the shared Accounts role check."""
from app.accounts.auth import role_required

admin_required = role_required("administrator")
