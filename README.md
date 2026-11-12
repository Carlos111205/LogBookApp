# Attachment Desk — NUST Computer Science

A local Django application for Computer Science students recording industrial attachment work. It stores placement details and daily log entries in Django's built-in SQLite database and builds Word or PDF exports.

## Run locally (Windows)

1. Install Python 3.10 or newer.
2. In this folder, run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   py manage.py migrate
   py manage.py runserver
   ```

3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

The database file `db.sqlite3` is created in this folder. Back it up to preserve student details and log entries. The optional Django admin is at `/admin/`; create an administrator with `py manage.py createsuperuser` if you want to use it.

## Vercel deployment

The settings accept Vercel's `VERCEL_URL`, `VERCEL_BRANCH_URL`, and `VERCEL_PROJECT_PRODUCTION_URL` as allowed hosts and HTTPS CSRF origins. In Vercel Project Settings, enable access to system environment variables and redeploy. Set `DJANGO_SECRET_KEY` to a strong random value and `DJANGO_DEBUG=0` for the deployment. If system variables are unavailable, set `DJANGO_ALLOWED_HOSTS` to the exact deployment hostname(s) and `DJANGO_CSRF_TRUSTED_ORIGINS` to their `https://` origins.

Vercel deployments require a persistent PostgreSQL database. Add a PostgreSQL integration from the Vercel project's **Storage** or **Marketplace** area and make sure it provides `DATABASE_URL`; when available, `DATABASE_URL_UNPOOLED` is used for deployment migrations. The Vercel build hook runs `py manage.py migrate --noinput` against that database. SQLite remains the local development database only; it is not persistent across Vercel serverless instances.

## Student accounts and privacy

Create a separate account for each student at `/accounts/signup/`. Profiles and log entries are owned by that account; dashboards, edits, deletes, and Word/PDF exports are filtered to the signed-in user. Signing out returns to the sign-in page.

Records from the earlier single-user version are preserved by the account migration but deliberately left unassigned, so no new account can see them by default. To transfer those old records to their actual owner, first create that student's account and run `py manage.py assign_legacy_data <username>` before entering new placement details. The command refuses to overwrite a profile that already contains student data or to guess when it finds multiple old profiles.

## Included

- Student, programme, host organisation, dates, and supervisors
- Daily activities, skills, challenges, and reflections
- Editable report sections with dated log entries automatically included
- Separate log book and report exports as `.docx` and PDF
- NUST Computer Science letterhead and crest in exports and app branding
- Django form validation, CSRF protection, admin, and SQLite storage

The report is a starting point. Follow current NUST and host-organisation submission requirements before submission. For public deployment, configure a strong `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, HTTPS, and a production WSGI server.
