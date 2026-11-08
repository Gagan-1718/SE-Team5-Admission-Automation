"""Registration age boundary and hostile/malformed input regressions."""
from datetime import date
import pytest
from app.accounts import routes
from app.accounts.models import User
from app.extensions import db
from .test_registration import registration_payload


@pytest.fixture
def frozen_today(monkeypatch):
    def freeze(value):
        class FrozenDate(date):
            @classmethod
            def today(cls):
                return value
        monkeypatch.setattr(routes, "date", FrozenDate)
    freeze(date(2026, 11, 8))
    return freeze


@pytest.mark.parametrize("birthday,expected", [("2010-11-08",201), ("2010-11-09",400), ("2010-11-07",201), ("2020-01-01",400)])
def test_registration_minimum_age_calendar_boundary(client, app, frozen_today, birthday, expected):
    response=client.post("/accounts/register",json=registration_payload(date_of_birth=birthday))
    assert response.status_code == expected
    if expected == 400:
        assert "at least 16" in response.json["message"]
        assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0


@pytest.mark.parametrize("today,birthday,expected", [(date(2025,2,28),"2009-03-01",400), (date(2025,3,1),"2009-03-01",201), (date(2024,2,29),"2008-02-29",201), (date(2024,2,28),"2008-02-29",400), (date(2024,3,1),"2008-02-29",201)])
def test_age_is_calendar_based_including_leap_day(client, frozen_today, today, birthday, expected):
    frozen_today(today)
    assert client.post("/accounts/register",json=registration_payload(date_of_birth=birthday)).status_code == expected


@pytest.mark.parametrize("field,value", [
    ("name",None),("name",123),("name",["Candidate"]),("name","  "),("name","12345"),("name","Alice<script>"),("name","Alice\nSmith"),("name","A"*121),
    ("email",None),("email",["a@example.test"]),("email","bad"),("email","bad\x00@example.test"),("email","a"*246+"@example.test"),
    ("mobile",1234567890),("mobile",True),("mobile","123456789"),("mobile","12345678901"),("mobile","１２３４５６７８９０"),
    ("password",[]),("password",12345678),("password","        "),("password","short"),("password","x"*129),
    ("date_of_birth","20101108"),("date_of_birth","2010-W45-1"),("date_of_birth","2010-02-30"),("date_of_birth",20100101),
])
def test_invalid_registration_inputs_are_rejected_without_saving(client, app, field, value):
    response=client.post("/accounts/register",json=registration_payload(**{field:value}))
    assert response.status_code == 400
    assert response.json["error"] == "validation_error"
    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0


@pytest.mark.parametrize("name",["Anne-Marie O'Neil", "R. Kumar", "ಅನನ್ಯ ಶೆಟ್ಟಿ"])
def test_realistic_names_and_normalized_email_are_accepted(client, name):
    response=client.post("/accounts/register",json=registration_payload(name=name,email=" CANDIDATE@EXAMPLE.TEST "))
    assert response.status_code == 201
    user=db.session.scalar(db.select(User))
    assert user.email == "candidate@example.test"
    assert user.name == name


def test_form_uses_server_age_cutoff_and_field_limits(client, frozen_today):
    html=client.get("/accounts/register").get_data(as_text=True)
    assert 'max="2010-11-08"' in html
    assert "at least 16 years old" in html
    assert 'maxlength="120"' in html
    assert 'maxlength="255"' in html
    assert 'maxlength="128"' in html
    assert 'maxlength="10"' in html
