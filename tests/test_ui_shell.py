"""Shared shell and friendly error-page coverage."""


def test_anonymous_home_has_product_story_and_public_actions(client):
    response = client.get("/")
    html = response.data.decode()
    assert response.status_code == 200
    assert "Feature modules are being added in Sprint One" not in html
    assert "From application to seat" in html
    assert 'href="/accounts/login"' in html
    assert 'href="/accounts/register"' in html


def test_error_pages_are_friendly_and_do_not_expose_tracebacks(client):
    for path, title in (("/missing-page", "Page not found"),):
        response = client.get(path)
        html = response.data.decode()
        assert response.status_code == 404
        assert title in html
        assert "Traceback" not in html
        assert 'href="/"' in html


def test_forbidden_page_is_friendly(app, client):
    with app.test_request_context("/"):
        response = app.make_response(app.handle_http_exception(__import__("werkzeug").exceptions.Forbidden()))
    assert response.status_code == 403
    assert b"Access denied" in response.get_data()
    assert b"Traceback" not in response.get_data()


def test_internal_error_page_is_friendly(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/__test-error")
    def _raise_error():
        raise RuntimeError("secret internal detail")

    response = client.get("/__test-error")
    assert response.status_code == 500
    assert b"Something went wrong" in response.get_data()
    assert b"secret internal detail" not in response.get_data()
    assert b"Traceback" not in response.get_data()
