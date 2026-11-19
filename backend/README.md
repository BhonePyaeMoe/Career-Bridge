# CareerBridge Django Project

CareerBridge is a role-based internship and entry-level job platform. The Django templates and Bootstrap pages still work alongside the REST API used by the Angular client. See [API.md](API.md) for endpoints and setup.

## Included features

- Student/company registration and login
- Role-based dashboards and permissions
- Student profiles, skills, and protected PDF CV downloads
- Company profiles with administrator approval
- Administrator-managed shared skill list
- Job creation, editing, closing, and administrator approval
- Public job search, filters, sorting, and pagination
- Apply-once transaction and database constraint
- Company applicant review and controlled status transitions
- Career Q&A with questions, answers, author editing, moderation, and accepted answers
- Django Admin management pages

## Setup on Windows PowerShell

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_skills
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

The admin panel is at `http://127.0.0.1:8000/admin/`.

When `createsuperuser` asks for the role, enter `admin`.

Run `python manage.py seed_skills` again whenever the provided skill list is updated. The command safely adds missing skills without duplicating existing ones.

## Approval workflow

1. A company registers and completes its profile.
2. The administrator approves it in **Admin → Companies**.
3. The approved company creates a job.
4. The administrator approves it in **Admin → Jobs**.
5. The approved job appears on the public job-search page.

## Career Q&A workflow

1. A logged-in student or company asks a question.
2. Other logged-in users submit answers.
3. Authors may edit their own questions and answers.
4. The question author may accept one answer.
5. Administrators may hide or restore content through Django Admin.

## Important notes

- SQLite is used during development. PostgreSQL can replace it during deployment.
- Uploaded CVs are not served as public media URLs. They are downloaded through a permission-protected Django view.
- Set `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` as environment variables before deployment.
- Set `DEBUG = False` and use HTTPS in production.
