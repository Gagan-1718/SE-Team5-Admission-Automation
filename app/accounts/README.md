# Accounts module interfaces

The Accounts module exposes the following stable interfaces to other modules:

- `current_identity()` returns the authenticated user's `id`, `role`, `rank`, and `category`, or `None`.
- `current_candidate_id()` returns an integer candidate ID only for an authenticated `candidate`; it returns `None` for anonymous users and administrators.
- `login_required` protects API endpoints and returns HTTP 401 for anonymous requests.
- `page_login_required` protects browser pages and redirects anonymous users to `/accounts/login?next=<path>`.
- `role_required("administrator")` protects administrator-only endpoints.
- `get_exam_details(candidate_id)` returns `exam_type`, `rank`, `category`, and `score`, or `None` when details have not been entered.

The exact role names are `candidate` and `administrator`.
