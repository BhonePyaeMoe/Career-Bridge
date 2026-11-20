CareerBridge
CareerBridge is a full-stack job board for students looking for internships and entry-level roles. Students can find jobs, save listings, and track applications. Companies can post vacancies and review applicants, while administrators approve companies and listings before they appear in public search.

Built by Bhone Pyae Moe and Naw Ei Hsu May Zaw for the Full Stack Application Development course at the Asian Institute of Technology.
What you can do
Role	Features
Student	Complete a profile, upload a CV, filter jobs, save listings privately, apply once per job, and track application status.
Company	Submit a company profile for approval, create and close listings, review applicants for your own jobs, and update their status or interview details.
Administrator	Approve company profiles and job listings, manage the shared skills list, and moderate Career Q&A.


Students and company users can ask and answer questions in Career Q&A. Saving a job does not submit an application. Students who already applied can revisit eligible closed listings from My applications without reopening the job to the public.
Tech stack
- Frontend: Angular and TypeScript
- Backend: Django and Django REST Framework
- Local database: SQLite
- Backend testing: pytest and pytest-django
Run locally
You need Python 3.12 or newer, plus Node.js 22.12+ (22.x) or 24.x with npm. The examples below use Windows PowerShell. On macOS or Linux, activate the virtual environment with source .venv/bin/activate instead.

Terminal 1 — Django (from the repository root):
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_skills
python manage.py runserver
Terminal 2 — Angular (from the repository root):
cd frontend
npm ci
npm start
Open CareerBridge and keep both terminals running. Angular is configured to proxy API requests to Django. To create a local administrator, run python manage.py createsuperuser from backend/ with the virtual environment active, enter admin if asked for the role, then sign in at Django Admin.
Try the main workflow
1. Register a company, complete its profile, and approve it in Django Admin.
2. As the company, create a listing with a future deadline, then approve it in Django Admin.
3. In a separate browser profile or private window, register a student, complete the profile, upload a sample PDF CV, and apply to the approved listing. Try saving the job before applying to see that bookmarks and applications are separate.
4. As the company, move the application to Under Review. Confirm the new status appears in the student’s My applications page.
Run tests and build the frontend
From backend/, with the virtual environment active:
python -m pip install -r requirements-test.txt
python -m pytest -q
The suite uses local test settings. It covers role and ownership checks, listing rules, application submission, bookmark privacy, and closed-listing access. Neither server needs to be running.

To check the frontend build, run npm run build from frontend/ after installing dependencies.
Project layout
- [`frontend/`](frontend/) — Angular pages and components
- [`backend/`](backend/) — Django models, REST API, Django Admin, and automated tests
- [`backend/API.md`](backend/API.md) — API reference
Planned improvements
- Send email notifications for application status changes and interview updates.
- Highlight jobs based on how many required skills match the student’s profile, and show the match count
