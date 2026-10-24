"""Prepare a clean local database for recording the Sprint One demo video (fictional data only).

    $env:ADMIN_SEED_PASSWORD = "demo-admin-password-1"
    $env:DEMO_CANDIDATE_PASSWORD = "demo-candidate-password-1"
    python scripts/prepare_demo.py --yes --with-candidate

What it does to YOUR LOCAL database (instance/team5_admission.db, or DATABASE_URL):
  1. drops every table and recreates them (all local data is deleted),
  2. runs the normal seeds (administrator, exam records, colleges, eligibility rules),
  3. optionally creates one ready-to-use demo candidate so the video does not spend time typing,
  4. deletes leftover uploaded files in instance/uploads/.
Passwords come from the environment and are never stored in Git. Nothing here touches other people's data.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEMO_CANDIDATE_EMAIL = "demo.candidate@example.test"
DEMO_CANDIDATE_MOBILE = "9123456780"
DEMO_CANDIDATE_NAME = "Asha Demo"
ADMIN_EMAIL = "admin@example.test"


def prepare_demo(app, with_candidate=False, candidate_password=None):
    """Reset the database of `app`, seed it, and optionally add the demo candidate."""
    from app.accounts.models import User
    from app.accounts.security import hash_password
    from app.extensions import db

    runner = app.test_cli_runner()
    for command in (["init-db", "--reset"], ["seed-db"]):
        result = runner.invoke(args=command)
        if result.exit_code != 0:
            raise RuntimeError(f"flask {' '.join(command)} failed:\n{result.output}")

    if with_candidate:
        if not candidate_password:
            raise ValueError("DEMO_CANDIDATE_PASSWORD is required with --with-candidate.")
        with app.app_context():
            db.session.add(User(name=DEMO_CANDIDATE_NAME, email=DEMO_CANDIDATE_EMAIL,
                                mobile=DEMO_CANDIDATE_MOBILE, role="candidate",
                                password_hash=hash_password(candidate_password)))
            db.session.commit()

    uploads = Path(app.config.get("DOCUMENT_UPLOAD_DIR") or Path(app.instance_path) / "uploads")
    if uploads.is_dir():
        shutil.rmtree(uploads)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--yes", action="store_true", help="confirm that the local database may be reset")
    parser.add_argument("--with-candidate", action="store_true", help="also create the demo candidate")
    args = parser.parse_args()
    if not args.yes:
        parser.error("this deletes your local database data; run again with --yes to confirm")
    if not os.environ.get("ADMIN_SEED_PASSWORD"):
        parser.error("set ADMIN_SEED_PASSWORD first (a fictional password for admin@example.test)")

    from app import create_app

    app = create_app()
    prepare_demo(app, args.with_candidate, os.environ.get("DEMO_CANDIDATE_PASSWORD"))
    print("Demo database is ready.")
    print(f"  Administrator : {ADMIN_EMAIL}  (password = ADMIN_SEED_PASSWORD)")
    if args.with_candidate:
        print(f"  Candidate     : {DEMO_CANDIDATE_EMAIL}  (password = DEMO_CANDIDATE_PASSWORD)")
    print("Start the site:  python scripts/serve_https.py   ->  https://localhost:8443")


if __name__ == "__main__":
    main()
