"""The standalone seat consistency check (issue #8)."""
import subprocess
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

from app.allotment.services import run_allotment
from app.catalogue.models import Seat
from app.extensions import db

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_seat_consistency.py"


def run_script(app):
    db.session.commit()
    path = make_url(app.config["SQLALCHEMY_DATABASE_URI"]).database
    return subprocess.run([sys.executable, str(SCRIPT), path], capture_output=True, text=True, timeout=120)


def test_script_says_consistent_after_a_run(app, oracle):
    run_allotment(oracle.admin.id)
    done = run_script(app)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "consistent" in done.stdout


def test_script_fails_and_names_a_corrupted_seat(app, oracle):
    run_allotment(oracle.admin.id)
    seat = oracle.seat("B-ECE")
    db.session.execute(db.update(Seat).where(Seat.id == seat.id).values(filled=1))
    done = run_script(app)
    assert done.returncode == 1
    assert f"MISMATCH seat row {seat.id}" in done.stdout
