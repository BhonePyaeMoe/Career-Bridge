# CareerBridge

CareerBridge is a full-stack job board for students looking for internships and entry-level roles. Students can find jobs, save listings, and track applications. Companies can post vacancies and review applicants, while administrators approve companies and listings before they appear in public search.

Built by Bhone Pyae Moe and Naw Ei Hsu May Zaw for the Full Stack Application Development course at the Asian Institute of Technology.

## Features

| Role | What you can do |
| --- | --- |
| Student | Complete a profile, upload a CV, filter jobs, bookmark listings, apply once per job, and track application status. |
| Company | Submit a company profile for approval, create and close listings, review applicants for your own jobs, and update their status or interview details. |
| Administrator | Approve company profiles and job listings, manage the shared skills list, and moderate Career Q&A. |

Students and company users can ask and answer questions in Career Q&A. Saving a job is private and does not submit an application. Students who already applied can revisit eligible closed listings from **My applications**.

## Tech Stack

- **Frontend:** Angular and TypeScript
- **Backend:** Django and Django REST Framework
- **Local database:** SQLite
- **Backend testing:** pytest and pytest-django

## Run Locally

You need Python 3.12 or newer and Node.js 22.12+ (22.x) or 24.x with npm. The commands below use Windows PowerShell. On macOS or Linux, use `source .venv/bin/activate` to activate the virtual environment instead.

### Terminal 1 — Django

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_skills
python manage.py runserver
```

### Terminal 2 — Angular

From the repository root:

```powershell
cd frontend
npm ci
npm start
```

Open [CareerBridge](http://localhost:4200/) and keep both terminals running. Angular forwards API requests to Django.

To create a local administrator, run `python manage.py createsuperuser` from `backend/` with the virtual environment active. Enter `admin` if asked for the role, then sign in at [Django Admin](http://localhost:8000/admin/).

## Try the Main Workflow

1. Register a company, complete its profile, and approve it in Django Admin.
2. As the company, create a job with a future deadline. Approve the listing in Django Admin.
3. In a separate browser profile or private window, register a student. Complete the profile, upload a sample PDF CV, and apply. Try bookmarking the job first to see that saving and applying are separate actions.
4. As the company, move the application to **Under Review**. Check that the new status appears in the student’s **My applications** page.

## Testing

From `backend/`, with the virtual environment active:

```powershell
python -m pip install -r requirements-test.txt
python -m pytest -q
```

The tests cover role permissions, listing rules, application submission, bookmark privacy, and access to closed listings. Neither server needs to be running.

To check the frontend build, run `npm run build` from `frontend/` after installing its dependencies.

## Project Structure

- [`frontend/`](frontend/) — Angular pages and components
- [`backend/`](backend/) — Django models, REST API, admin interface, and tests
- [`backend/API.md`](backend/API.md) — API reference

## Planned Improvements

- Send email notifications for application status changes and interview updates.
- Highlight jobs that match a student’s skills and show how many required skills match.
