# Team 5 Admission Automation

The implementation uses Python 3.12, Flask, SQLite and simple HTML/CSS pages served by the same application. The system uses fictional exam data and supports one admission counselling cycle. It has candidate and administrator roles.

Start with SPRINT_ONE_START_HERE.md for responsibilities and the proposed October 19–23 schedule. Follow the existing SRS for requirements, SAD_Python.md for architecture and TEST_PLAN_PYTHON_ADDENDUM.md alongside the original test cases. DOCUMENT_CHANGE_RECORD.md explains revision status. Differences between what we built and the submitted SRS, SAD and test plan are listed in docs/DEVIATIONS.md; test evidence is in docs/evidence/. A GitHub Actions check (.github/workflows/ci.yml) runs the tests on every push and pull request.

## Status

Merged into `main`: shared Flask foundation, accounts (registration, login, roles, seeded exam details), application draft and submission, documents (upload, administrator review, resubmission), the college catalogue, eligibility rules, HTTPS and a CI check. Eligibility still runs on sample inputs, and the audit log, the admin dashboard and some links between modules are not finished. **`python -m pytest -q tests/integration/test_demo_flow.py -rx` is the live checklist:** the passing test is the working demo flow, and every item listed as XFAIL says what is still missing and who owns it. Acceptance tests TC-001 to TC-030 are only marked passed in `docs/evidence/` after they were actually run.

### Application module (draft and submission, issues #2 and #3)

You must be logged in as a candidate. Register and log in at `/accounts/register` and `/accounts/login`; anonymous visitors are sent to the login page, and administrators are refused (403). Then open `/application` to save and resume a draft: your draft is kept when you log out and log in again. Press **Submit application** once every field is filled in. Submitting gives a unique reference number such as `ADM-2026-000001` and locks the application.

JSON endpoints follow the SAD: `POST /api/v1/applications`, `PUT /api/v1/applications/<id>`, `GET /api/v1/applications/me`, `POST /api/v1/applications/<id>/submit` (401 when not logged in, 403 for another candidate's application).

For other modules: `app.application.services.get_for_candidate(candidate_id)` and `get_submitted_application(candidate_id)` (returns the application only when it is Submitted). `applications.candidate_id` is a foreign key to `users.id`, so if you created a local database before this change, run `flask --app app init-db --reset` once. The form fields (guardian name/mobile, school, board, percentage) are provisional until the team agrees the final list.

## Run it locally (Windows PowerShell)

You need Git and Python 3.12.

```powershell
git clone https://github.com/Gagan-1718/SE-Team5-Admission-Automation.git
cd SE-Team5-Admission-Automation
git checkout 31-set-up-shared-spring-boot-app-and-mysql-connection

py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

flask --app app init-db
flask --app app seed-db
pytest
flask --app app run
```

Open <http://127.0.0.1:5000/> for the home page and <http://127.0.0.1:5000/health> for the health check (`{"database":"ok","status":"ok"}`). Press Ctrl+C to stop the server.

If PowerShell refuses to run `Activate.ps1`, use `.venv\Scripts\python -m pip ...`, `.venv\Scripts\python -m flask ...` and `.venv\Scripts\python -m pytest` instead of activating.

macOS/Linux (same steps, not yet run by the team): create the environment with `python3.12 -m venv .venv` and activate it with `source .venv/bin/activate`.

## Run it over HTTPS (issue #4)

Flask's own `flask run` server is plain HTTP and is only for development. For the HTTPS demonstration the app is served by Cheroot with a locally generated, self-signed certificate (valid for `localhost` and `127.0.0.1`).

```powershell
pip install -r requirements-https.txt
python scripts/serve_https.py
```

Open <https://localhost:8443/>. Your browser warns that the certificate is self-signed: that is expected in the lab, so choose to continue. Plain `http://localhost:8080/` redirects to HTTPS. Only TLS 1.2 or newer is accepted, HTTPS responses carry `Strict-Transport-Security`, and the login cookie is marked `Secure` when served over HTTPS. Use `--https-port` and `--http-port` to change the ports.

The certificate and private key are created once in `instance/certs/`, which is ignored by Git. Never commit them. The HTTPS tests (`python -m pytest -q tests/test_https.py`) start the real server and record the bytes on the network to show that a password is not visible; they are skipped automatically if `requirements-https.txt` is not installed.

## Demo walkthrough (Sprint One)

Everything uses fictional data. In PowerShell, from the project folder with the virtual environment active:

```powershell
$env:ADMIN_SEED_PASSWORD = "choose-a-fictional-password"
flask --app app init-db --reset
flask --app app seed-db
python scripts/serve_https.py      # HTTPS on https://localhost:8443 (see the HTTPS section), or: flask --app app run
```

`seed-db` creates the administrator `admin@example.test` (password = what you put in `ADMIN_SEED_PASSWORD`), the fictional exam records, two colleges with branches and seats, and the eligibility cut-offs. Candidates register themselves.

Exam details a candidate can enter (only these exact combinations exist; anything else is refused):

| Exam | Rank | Category | Score |
|---|---|---|---|
| KCET | 1000 | General | 185.0 |
| KCET | 4500 | OBC | 160.5 |
| KCET | 12000 | SC | 140.0 |
| KCET | 15000 | ST | 132.5 |
| KCET | 9000 | EWS | 150.0 |
| KCET | 90000 | General | 60.0 |
| COMEDK | 800 | General | 190.0 |
| COMEDK | 6000 | OBC | 155.0 |

Flow: register at `/accounts/register`, log in, enter the exam details (the profile page has no exam-details form yet, so for now send `PUT /accounts/exam-details` with `exam_type`, `rank`, `category` and `score`; the form is being added), open `/application` and save a draft, log out and in again (the draft is still there), submit (you get a reference such as `ADM-2026-000001`), upload the three documents (Marksheet, ID Proof, Category Certificate; PDF, JPEG or PNG up to 2 MB), then log in as the administrator at `/admin/documents` to approve, or reject with a reason. The candidate sees the reason on `/documents` and can resubmit. Candidates browse colleges at `/colleges`.

## Database commands

| Command | What it does |
|---|---|
| `flask --app app init-db` | Creates all tables. Safe to run repeatedly. |
| `flask --app app init-db --reset` | Drops every table first, then recreates them. Your local data is lost. |
| `flask --app app seed-db` | Adds fictional seed data. Safe to run repeatedly (no duplicates). |

Each developer has their own SQLite file at `instance/team5_admission.db`. Never commit it, and never share it through Git. Set `DATABASE_URL` (for example `sqlite:///C:/temp/mine.db`) to use a different file. Tests always use a temporary database and never touch yours.

`SECRET_KEY` can be set as an environment variable. If it is not set, a random key is created in `instance/secret_key.txt` the first time the app starts. The `instance/` folder is ignored by Git.

## Project layout

```
app/
  __init__.py       application factory (create_app)
  extensions.py     the one shared SQLAlchemy object (db) + SQLite foreign keys
  main.py           home page and /health
  cli.py            init-db and seed-db commands
  setup_check.py    fictional smoke-test table (remove once real modules cover it)
  accounts/         Varun
  application/      Gagan
  documents/        Dikshith
  catalogue/        Tasya
  eligibility/      Tasya
config.py           configuration (no secrets)
templates/          Jinja templates (base.html, home.html, one folder per module)
static/             CSS
tests/              pytest tests (one folder per module)
```

## Adding your module

Work only in your own module folder, on your own branch. You do not need to edit any shared file. The app looks for these optional files in your module and loads them automatically:

| File | Purpose |
|---|---|
| `app/<module>/models.py` | Your SQLAlchemy models. Use `from app.extensions import db`. Tables are created by `init-db`. |
| `app/<module>/routes.py` | A Flask `Blueprint` named `bp`. It is registered automatically. |
| `app/<module>/seed.py` | A `seed()` function that is safe to run repeatedly. `seed-db` calls it. |

Rules the team agreed: one owner per module, no direct work on `main`, fictional data only, and no database files, uploads, virtual environments or secrets in Git. Keep the shared contract names unchanged (see the sprint guide).

## Run the tests

```powershell
pytest
```

## Integrated candidate documents

After signing in, open My application and submit it. The submitted page links to
Upload documents and My documents. Upload/resubmission use the current candidate
and their Submitted application. Administrators sign in through the same login
page and are sent to Review documents; candidates cannot access review/download
routes. The header provides navigation and logout.

The old DOCUMENT_DEV_FIXTURE and DOCUMENTS_ADMIN_GUARD settings no longer grant
document access. No fixed candidate or application ID is used by document routes.

Use an existing administrator account, or run the existing seed-db command for
fictional demo data. On first creation, its password comes from ADMIN_SEED_PASSWORD
or is printed by the seed command; seeding does not reset an existing password.
Never reset the database to test integration.

See ADM_F_008_VERIFICATION.md for test coverage and outstanding team integration.


## Document integrity upgrade (24 October 2026)

New databases include foreign keys from documents.candidate_id to users.id and
documents.application_id to applications.id. The upload page offers only
Marksheet, ID Proof and Category Certificate; the server rejects other types
before creating metadata or saving a file. Existing legacy document types are
preserved by the migration and are not silently renamed.

For an existing local SQLite database, stop the server and back up its database
and uploads first. If DATABASE_URL is set, back up that database instead of the
default instance/team5_admission.db. Keep backups outside Git.

Then run from the repository root:

~~~powershell
.\.venv\Scripts\python.exe -m flask --app app upgrade-document-references
~~~

This command preserves document IDs, metadata and upload files and is safe to
repeat. It stops without changing rows if a document references a missing user
or application. Repair those references before retrying; do not reset the database.
init-db alone does not alter tables that already exist. This upgrade has been
tested on temporary databases; it has not been applied to your personal database.

See docs/evidence/dikshith.md for executed TC-006/007/008/022 checks.
