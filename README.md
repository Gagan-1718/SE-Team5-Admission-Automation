# Team 5 Admission Automation

The implementation uses Python 3.12, Flask, SQLite and simple HTML/CSS pages served by the same application. The system uses fictional exam data and supports one admission counselling cycle. It has candidate and administrator roles.

Start with SPRINT_ONE_START_HERE.md for responsibilities and the proposed October 19–23 schedule. Follow the existing SRS for requirements, SAD_Python.md for architecture and TEST_PLAN_PYTHON_ADDENDUM.md alongside the original test cases. DOCUMENT_CHANGE_RECORD.md explains revision status.

## Status

The shared Flask foundation (application factory, SQLite, home page, `/health`, database commands and startup tests) is in place for review under issue #31. Feature modules (accounts, application, documents, catalogue, eligibility) are still being built by their owners. Acceptance tests TC-001 to TC-030 have not been executed yet.

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
