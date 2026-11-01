"""The allotment timing script (issue #7, TC-027) on a small dataset."""
import tempfile
from pathlib import Path

from scripts import time_allotment


def test_the_script_times_clean_runs_and_passes(monkeypatch, capsys):
    monkeypatch.setenv("DEMO_CANDIDATE_PASSWORD", "test-demo-password")
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "test-admin-password")
    made = []
    real_mkdtemp = tempfile.mkdtemp
    monkeypatch.setattr(tempfile, "mkdtemp", lambda **kw: made.append(real_mkdtemp(**kw)) or made[-1])
    assert time_allotment.main(["--candidates", "20", "--runs", "2"]) == 0
    assert len(made) == 1 and not Path(made[0]).exists()  # every database file was deleted
    out = capsys.readouterr().out
    # both runs start from the same clean copy, so they give the same outcome
    runs = [line.split(", ", 1)[1] for line in out.splitlines() if line.startswith("Run ")]
    assert len(runs) == 2 and runs[0] == runs[1]
    assert "processed 14," in runs[0] and "seats consistent" in runs[0]
    assert "median" in out and out.rstrip().endswith("PASS")


def test_the_script_fails_when_a_run_is_over_the_limit(monkeypatch, capsys):
    monkeypatch.setenv("DEMO_CANDIDATE_PASSWORD", "test-demo-password")
    monkeypatch.setenv("ADMIN_SEED_PASSWORD", "test-admin-password")
    monkeypatch.setattr(time_allotment, "LIMIT_SECONDS", 0)
    assert time_allotment.main(["--candidates", "10", "--runs", "1"]) == 1
    assert capsys.readouterr().out.rstrip().endswith("FAIL")
