"""The navigation bar shows the right links for each kind of visitor."""
import re

from app.accounts.models import User
from app.accounts.security import hash_password
from app.extensions import db

PASSWORD = "fictional-password-1"


def nav_links(client):
    html = client.get("/").data.decode()
    return re.findall(r'<a(?:\s+[^>]*?)?\s+href="([^"]+)"', html.split("<main")[0])


def login(app, email, role, mobile):
    db.session.add(User(name="Fictional " + role, email=email, mobile=mobile, role=role,
                        password_hash=hash_password(PASSWORD)))
    db.session.commit()
    client = app.test_client()
    response = client.post("/accounts/login", json={"identifier": email, "password": PASSWORD})
    assert response.status_code == 200
    return client


def test_anonymous_visitor_sees_login_and_register(client):
    links = nav_links(client)
    assert "/accounts/login" in links and "/accounts/register" in links
    assert "/application" not in links


def test_candidate_sees_catalogue_eligibility_and_own_pages(app):
    links = nav_links(login(app, "nav.candidate@example.test", "candidate", "9000000011"))
    for expected in ("/dashboard", "/accounts/profile-page", "/application", "/documents", "/colleges", "/eligibility", "/choices", "/result"):
        assert expected in links
    assert "/admin/documents" not in links and "/admin/colleges" not in links


def test_administrator_review_link_opens_the_page_not_the_json(app):
    links = nav_links(login(app, "nav.admin@example.test", "administrator", "9000000012"))
    for expected in ("/admin/dashboard", "/admin/documents", "/admin/colleges", "/admin/audit-logs", "/admin/candidates", "/admin/eligibility-rules", "/admin/allotment"):
        assert expected in links
    assert "/admin/documents.json" not in links
    assert "/application" not in links


def test_locked_navigation_has_explanation_and_lock_indicator(app):
    client = login(app, "nav.locked@example.test", "candidate", "9000000013")
    html = client.get("/").data.decode()
    assert 'href="/choices"' in html
    assert 'title="Choice filling opens after eligibility is confirmed."' in html
    assert 'aria-describedby="lock-choices"' in html
    assert 'data-locked' in html
    assert 'aria-label="Locked"' in html


def test_locked_navigation_stays_focusable_but_prevents_activation(app):
    html = login(app, "nav.prevent@example.test", "candidate", "9000000015").get("/").data.decode()
    assert 'class="app-nav-link locked"' in html
    assert 'href="/choices"' in html
    assert "event.preventDefault()" in html


def test_navigation_uses_real_anchor_links(app):
    html = login(app, "nav.anchor@example.test", "candidate", "9000000014").get("/").data.decode()
    assert re.search(r'<a[^>]+href="/application"', html)
