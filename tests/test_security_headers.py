"""Response security headers (SEC-F-004)."""


def test_nosniff_header_is_sent(client):
    assert client.get("/health").headers["X-Content-Type-Options"] == "nosniff"


def test_hsts_is_not_sent_over_plain_http(client):
    assert "Strict-Transport-Security" not in client.get("/health").headers


def test_hsts_is_sent_over_https(client):
    response = client.get("/health", base_url="https://localhost")
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
