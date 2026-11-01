"""The real allotment run on the database (issues #5, #6, #8; TC-015, TC-016, TC-028)."""
import threading

import pytest
from sqlalchemy.exc import IntegrityError

from app.allotment import services
from app.allotment.models import ALLOCATED, NOT_ALLOCATED, AllotmentResult, AllotmentRun
from app.allotment.services import (
    AlreadyCompleted, NothingToAllot, RunFailed, get_completed_run, get_result_for_candidate,
    run_allotment, seat_consistency_report,
)
from app.audit.models import AuditLog
from app.catalogue.models import Seat
from app.extensions import db


def result_of(world, label):
    return get_result_for_candidate(world.candidates[label].id)


def counts():
    return (db.session.query(AllotmentRun).count(), db.session.query(AllotmentResult).count())


def all_filled():
    db.session.expire_all()
    return sorted(s.filled for s in db.session.query(Seat).all())


# ------------------------------------------------------------ TC-015 / TC-016 oracle
def test_oracle_through_the_database(oracle):
    summary = run_allotment(oracle.admin.id)

    expected = {"C1": ("A-CSE", 1), "C2": ("A-CSE", 1), "C3": ("A-ISE", 2), "C4": None, "C5": None}
    for label, outcome in expected.items():
        r = result_of(oracle, label)
        if outcome is None:
            assert (r.status, r.branch_id, r.seat_id, r.choice_priority) == (NOT_ALLOCATED, None, None, None)
        else:
            key, priority = outcome
            assert r.status == ALLOCATED
            assert r.branch_id == oracle.branches[key].id and r.choice_priority == priority
            assert r.seat_id == oracle.seat(key).id

    assert oracle.seat("A-CSE").filled == 2
    assert oracle.seat("A-ISE").filled == 1
    assert oracle.seat("B-ECE").filled == 0  # unchanged: one seat still free
    assert (summary.candidates_processed, summary.allocated_count, summary.not_allocated_count) == (5, 3, 2)
    assert get_completed_run().id == summary.run_id


def test_results_keep_rank_category_and_reference(oracle):
    run_allotment(oracle.admin.id)
    r = result_of(oracle, "C3")
    assert (r.rank, r.category) == (3, "General")
    assert r.reference_number.startswith("ADM-2026-")


def test_the_run_is_audited_in_the_same_commit(oracle):
    summary = run_allotment(oracle.admin.id)
    entry = db.session.query(AuditLog).filter_by(action_type="allotment.run").one()
    assert (entry.actor_id, entry.target_type, entry.target_id, entry.outcome) == (
        oracle.admin.id, "allotment_run", summary.run_id, "Success")


def test_the_consistency_report_is_empty_after_a_run(oracle):
    run_allotment(oracle.admin.id)
    assert seat_consistency_report() == []


# ------------------------------------------------------------ who takes part (D2-06)
def test_a_not_eligible_candidate_is_skipped_and_takes_no_seat(world):
    world.branch("A-CSE", {"General": 1})
    world.candidate("Late", 90000, ["A-CSE"])   # rank 90000 is above the General cut-off 20000
    world.candidate("Ok", 500, ["A-CSE"])
    run_allotment(world.admin.id)
    assert result_of(world, "Late") is None     # not part of the run, not "Not Allocated"
    assert result_of(world, "Ok").status == ALLOCATED


def test_a_candidate_with_a_document_still_pending_is_skipped(world):
    world.branch("A-CSE", {"General": 1})
    world.candidate("Pending", 1, ["A-CSE"], documents="Pending")
    world.candidate("Ok", 2, ["A-CSE"])
    run_allotment(world.admin.id)
    assert result_of(world, "Pending") is None
    assert result_of(world, "Ok").status == ALLOCATED


def test_a_candidate_who_never_locked_is_skipped(world):
    world.branch("A-CSE", {"General": 1})
    world.candidate("Open", 1, ["A-CSE"], locked=False)
    world.candidate("Ok", 2, ["A-CSE"])
    run_allotment(world.admin.id)
    assert result_of(world, "Open") is None
    assert result_of(world, "Ok").status == ALLOCATED


def test_category_seats_are_used_only_by_that_category(world):
    world.branch("A-CSE", {"General": 1, "OBC": 1})
    world.candidate("G1", 1, ["A-CSE"])
    world.candidate("G2", 2, ["A-CSE"])
    world.candidate("O1", 3, ["A-CSE"], category="OBC")
    run_allotment(world.admin.id)
    assert result_of(world, "G2").status == NOT_ALLOCATED
    assert result_of(world, "O1").status == ALLOCATED
    assert world.seat("A-CSE", "OBC").filled == 1


def test_comedk_and_kcet_ranks_are_compared_as_stored(world):
    """Agreed behaviour (SAD A-10): COMEDK 800 is processed before KCET 1000."""
    world.branch("A-CSE", {"General": 1})
    world.candidate("Kcet", 1000, ["A-CSE"], exam_type="KCET")
    world.candidate("Comedk", 800, ["A-CSE"], exam_type="COMEDK")
    run_allotment(world.admin.id)
    assert result_of(world, "Comedk").status == ALLOCATED
    assert result_of(world, "Kcet").status == NOT_ALLOCATED


# ------------------------------------------------------------ refusals
def test_a_second_run_is_refused_and_changes_nothing(oracle):
    run_allotment(oracle.admin.id)
    before = (counts(), all_filled())
    with pytest.raises(AlreadyCompleted):
        run_allotment(oracle.admin.id)
    assert (counts(), all_filled()) == before


def test_nobody_locked_means_no_run_and_no_audit(world):
    world.branch("A-CSE", {"General": 1})
    world.candidate("Open", 1, ["A-CSE"], locked=False)
    with pytest.raises(NothingToAllot):
        run_allotment(world.admin.id)
    assert counts() == (0, 0)
    assert db.session.query(AuditLog).filter_by(action_type="allotment.run").count() == 0


def test_only_ineligible_locked_candidates_is_also_nothing_to_allot(world):
    world.branch("A-CSE", {"General": 1})
    world.candidate("Late", 90000, ["A-CSE"])
    with pytest.raises(NothingToAllot):
        run_allotment(world.admin.id)
    assert get_completed_run() is None


# ------------------------------------------------------------ failure and rollback (A-07)
def test_a_failure_halfway_leaves_nothing_behind_and_is_audited_as_failed(oracle, monkeypatch):
    real_record_audit = services.record_audit

    def fail_inside_the_run(*args, commit=True, **kwargs):
        if commit is False:  # the in-transaction audit entry, after seats and results are written
            raise RuntimeError("deliberate failure for the rollback test")
        return real_record_audit(*args, commit=commit, **kwargs)

    monkeypatch.setattr(services, "record_audit", fail_inside_the_run)
    with pytest.raises(RunFailed):
        run_allotment(oracle.admin.id)

    assert counts() == (0, 0)
    assert all_filled() == [0, 0, 0]
    assert get_completed_run() is None
    failed = db.session.query(AuditLog).filter_by(action_type="allotment.run").one()
    assert failed.outcome == "Failed"
    # and the run can be repeated after a failure (A-13)
    monkeypatch.setattr(services, "record_audit", real_record_audit)
    assert run_allotment(oracle.admin.id).allocated_count == 3


def test_two_runs_at_the_same_time_produce_exactly_one(app, oracle):
    admin_id = oracle.admin.id
    db.session.commit()
    outcomes = []

    def attempt():
        with app.app_context():
            try:
                run_allotment(admin_id)
                outcomes.append("ran")
            except (AlreadyCompleted, RunFailed) as exc:
                outcomes.append(type(exc).__name__)
            finally:
                db.session.remove()

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert outcomes.count("ran") == 1, outcomes
    db.session.expire_all()
    assert counts() == (1, 5)
    assert seat_consistency_report() == []


# ------------------------------------------------------------ consistency (#8, TC-028)
def test_the_report_names_a_seat_whose_count_does_not_match(oracle):
    run_allotment(oracle.admin.id)
    seat = oracle.seat("B-ECE")
    db.session.execute(db.update(Seat).where(Seat.id == seat.id).values(filled=1))
    db.session.commit()
    report = seat_consistency_report()
    assert [m["seat_id"] for m in report] == [seat.id]
    assert (report[0]["filled"], report[0]["allocated_records"]) == (1, 0)


def test_the_database_refuses_more_filled_than_capacity(oracle):
    seat = oracle.seat("A-ISE")
    with pytest.raises(IntegrityError):
        db.session.execute(db.update(Seat).where(Seat.id == seat.id).values(filled=seat.capacity + 1))
        db.session.commit()


def test_the_run_takes_the_write_lock_before_reading(app, world):
    """SAD A-07: while a run holds the transaction, no other connection can start writing."""
    import sqlite3

    from sqlalchemy.engine import make_url

    path = make_url(app.config["SQLALCHEMY_DATABASE_URI"]).database
    services._begin_write_transaction()
    other = sqlite3.connect(path, timeout=0.2)
    try:
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            other.execute("BEGIN IMMEDIATE")
    finally:
        other.close()
        db.session.rollback()
