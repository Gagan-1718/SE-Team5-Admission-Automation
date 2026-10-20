"""Response security headers (SEC-F-004)."""


def register_security(app):
    @app.after_request
    def add_security_headers(response):
        from flask import request

        # Tell browsers to keep using HTTPS for this site (only sent over HTTPS).
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response
