"""Time the allotment run on the demo dataset (issue #7, TC-027, ADM-NFR-002).

Usage (from the project folder, virtual environment active):
    python scripts/time_allotment.py                   # 300 candidates, 3 runs
    python scripts/time_allotment.py --candidates 600

Builds the seeded database and Tasya's fictional dataset once in a temporary folder,
then copies that database for each run, so every run starts from the same clean state
(no run yet, every seat filled = 0). Prints min, median and max seconds and exits with
code 1 if any run is slower than the limit or leaves the seat counts inconsistent.
Nothing is written to instance/ and the temporary folder is deleted at the end.
"""
import argparse
import os
import platform
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LIMIT_SECONDS = 60


def make_app(database, uploads):
    from app import create_app

    return create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + database.as_posix(),
        "DOCUMENT_UPLOAD_DIR": str(uploads),
    })


def build_dataset(database, uploads, candidates, seed):
    from app import MODULES, import_optional
    from app.extensions import db
    from app.setup_check import seed as seed_setup_check
    from scripts.make_demo_dataset import generate_dataset

    app = make_app(database, uploads)
    with app.app_context():
        db.create_all()
        seed_setup_check()
        for name in MODULES:
            module_seed = import_optional(f"app.{name}.seed")
            if module_seed is not None:
                module_seed.seed()
        generate_dataset(candidates, seed)
        db.session.remove()
        db.engine.dispose()


def timed_run(database, uploads):
    from app.accounts.models import User
    from app.allotment.services import run_allotment, seat_consistency_report
    from app.extensions import db

    app = make_app(database, uploads)
    with app.app_context():
        admin = db.session.execute(
            db.select(User).where(User.role == "administrator")).scalars().first()
        start = time.perf_counter()
        summary = run_allotment(admin.id)
        seconds = time.perf_counter() - start
        report = seat_consistency_report()
        db.session.remove()  # release the connection so Windows can delete the file
        db.engine.dispose()
    return seconds, summary, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Time the allotment run on the demo dataset.")
    parser.add_argument("--candidates", type=int, default=300, help="multiple of 10 (default 300)")
    parser.add_argument("--runs", type=int, default=3, help="number of timed runs (default 3)")
    parser.add_argument("--seed", type=int, default=1, help="dataset seed (default 1)")
    args = parser.parse_args(argv)

    # Fictional passwords for the temporary database only; never used anywhere else.
    os.environ.setdefault("DEMO_CANDIDATE_PASSWORD", "timing-only-fictional-pass")
    os.environ.setdefault("ADMIN_SEED_PASSWORD", "timing-only-fictional-admin")

    work = Path(tempfile.mkdtemp(prefix="team5-timing-"))
    try:
        template, uploads = work / "template.db", work / "uploads"
        print(f"Building {args.candidates} candidates (seed {args.seed}) ...")
        build_start = time.perf_counter()
        build_dataset(template, uploads, args.candidates, args.seed)
        print(f"Dataset built in {time.perf_counter() - build_start:.1f} s")

        times, failures = [], 0
        for number in range(1, args.runs + 1):
            database = work / f"run{number}.db"
            shutil.copyfile(template, database)
            seconds, summary, report = timed_run(database, uploads)
            times.append(seconds)
            consistent = "consistent" if not report else f"{len(report)} MISMATCHES"
            print(f"Run {number}: {seconds:.3f} s, processed {summary.candidates_processed}, "
                  f"allocated {summary.allocated_count}, not allocated {summary.not_allocated_count}, "
                  f"seats {consistent}")
            if report or seconds >= LIMIT_SECONDS:
                failures += 1

        print(f"\nCandidates in dataset: {args.candidates}")
        print(f"min {min(times):.3f} s, median {statistics.median(times):.3f} s, max {max(times):.3f} s "
              f"(limit {LIMIT_SECONDS} s)")
        print(f"Machine: {platform.system()} {platform.release()}, {platform.processor() or platform.machine()}, "
              f"Python {platform.python_version()}")
        print("PASS" if not failures else "FAIL")
        return 1 if failures else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
