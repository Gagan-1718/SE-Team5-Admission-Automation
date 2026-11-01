"""Check that seat counts match the allotment records (issue #8, TC-028, ADM-NFR-003).

Usage (from the project folder, virtual environment active):
    python scripts/check_seat_consistency.py                 # the configured database
    python scripts/check_seat_consistency.py path/to/file.db  # any other SQLite file

Prints one line per mismatch and exits with code 1 if there is any, otherwise prints
"consistent" and exits with 0. It only reads; it never changes the database.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main(argv):
    if len(argv) > 1:
        os.environ["DATABASE_URL"] = "sqlite:///" + Path(argv[1]).resolve().as_posix()

    from app import create_app
    from app.allotment.services import get_completed_run, seat_consistency_report

    app = create_app()
    with app.app_context():
        run = get_completed_run()
        report = seat_consistency_report()
    if run is None:
        print("No allotment run yet; every seat must still have filled = 0.")
    for m in report:
        print(f"MISMATCH seat row {m['seat_id']} (branch {m['branch_id']}, {m['category']}): "
              f"filled {m['filled']}, allotment records {m['allocated_records']}, capacity {m['capacity']}")
    if report:
        return 1
    print("consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
