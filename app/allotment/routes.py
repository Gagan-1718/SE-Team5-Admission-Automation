"""Allotment console and API (owner: Gagan).

HTML:  GET /admin/allotment            check, run, review (publishing is the Result module's card)
       POST /admin/allotment/run       run from the console, then back to the console
JSON:  POST /api/v1/admin/allotment/run   {runId, candidatesProcessed, allocatedCount,
                                           notAllocatedCount, durationMs}
Errors use the team's body {status, error, message} (SAD A-20).
Like every /admin/ route (TC-022 test): anonymous 401, candidate 403.
"""
from http import HTTPStatus

from flask import Blueprint, flash, g, jsonify, redirect, render_template, url_for

from app.accounts.auth import role_required
from app.catalogue.models import Seat
from app.extensions import db

from . import services

bp = Blueprint("allotment", __name__)



def _summary_json(summary):
    return {
        "runId": summary.run_id,
        "candidatesProcessed": summary.candidates_processed,
        "allocatedCount": summary.allocated_count,
        "notAllocatedCount": summary.not_allocated_count,
        "durationMs": summary.duration_ms,
    }


def _is_published(run):
    """Asks the Result module; until its function exists the console just says 'not yet'."""
    try:
        from app.results.services import is_published
        return bool(is_published(run.id))
    except NotImplementedError:
        return False


def _console_context():
    run = services.get_completed_run()
    seats = db.session.execute(db.select(Seat)).scalars().all()
    total_seats = sum(s.capacity for s in seats)
    candidates = services.load_candidates() if run is None else []
    ready = sum(1 for c in candidates if c["eligible"])

    checks = [
        {"label": "Seat matrix configured",
         "ok": total_seats > 0,
         "detail": f"{len(seats)} seat rows, {total_seats} seats in total"},
        {"label": "Eligible candidates with locked choices",
         "ok": run is not None or ready > 0,
         "detail": f"{ready} ready" if run is None else "Taken into the run"},
        {"label": "No allotment run yet",
         "ok": run is None,
         "detail": "This cycle can run once" if run is None else "Already completed"},
    ]
    can_run = run is None and all(c["ok"] for c in checks)

    branches = {}
    for seat in seats:
        label = f"{seat.branch.college.name} · {seat.branch.name}"
        row = branches.setdefault(label, {"label": label, "filled": 0, "capacity": 0})
        row["filled"] += seat.filled
        row["capacity"] += seat.capacity

    published = _is_published(run) if run else False
    steps = [
        {"label": "1. Pre-run checks", "state": "done" if (run or can_run) else "problem",
         "detail": "Passed" if (run or can_run) else "Fix the failed check below"},
        {"label": "2. Run allotment", "state": "done" if run else ("current" if can_run else "locked"),
         "detail": f"Done in {run.duration_ms / 1000:.1f} s" if run else "Runs once and cannot be repeated"},
        {"label": "3. Review result", "state": ("done" if published else "current") if run else "locked",
         "detail": "Check the numbers and the consistency check"},
        {"label": "4. Publish", "state": "done" if published else "locked",
         "detail": "Candidates can now see results" if published else "After review"},
    ]
    return {
        "run": run,
        "checks": checks,
        "can_run": can_run,
        "steps": steps,
        "branches": sorted(branches.values(), key=lambda b: b["label"]),
        "report": services.seat_consistency_report() if run else None,
        "published": published,
        "seat_rows": len(seats),
        "total_seats": total_seats,
    }


@bp.get("/admin/allotment")
@role_required("administrator")
def console():
    return render_template("allotment/console.html", **_console_context())


@bp.post("/admin/allotment/run")
@role_required("administrator")
def run_from_console():
    try:
        summary = services.run_allotment(g.current_user.id)
    except services.AllotmentError as exc:
        flash(str(exc), "error")
    else:
        flash(f"Allotment complete: {summary.allocated_count} allocated, "
              f"{summary.not_allocated_count} not allocated.")
    return redirect(url_for("allotment.console"), code=303)


@bp.post("/api/v1/admin/allotment/run")
@role_required("administrator")
def run_api():
    try:
        summary = services.run_allotment(g.current_user.id)
    except services.AllotmentError as exc:
        code = exc.status_code
        return jsonify(status=code, error=HTTPStatus(code).phrase, message=str(exc)), code
    return jsonify(_summary_json(summary))
