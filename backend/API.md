# CareerBridge API

The API shares the database with the Django HTML pages and uses the existing Django forms to validate changes. The new endpoints do not require additional migrations on an up-to-date database.

With your backend virtual environment active:

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py test api
python manage.py runserver
```

Try `/api/jobs/`, `/api/options/`, and `/api/forum/questions/` in the browser. The routes in the first table use `GET`.

| Access | Path | Response |
|---|---|---|
| Public | `/api/auth/session/` | Login state and, if logged in, account ID, username and role |
| Public | `/api/options/` | Skills, job types, work modes and university choices |
| Public | `/api/jobs/` | Approved jobs from approved companies with deadlines today or later |
| Public | `/api/jobs/{id}/` | Job details and `already_applied` for the current visitor |
| Public | `/api/forum/questions/` | Visible questions and their visible answer counts |
| Public | `/api/forum/questions/{id}/` | Visible question and its visible answers |
| Student | `/api/student/profile/` | Own profile (including any saved photo URL) in `profile`, or `null` if no profile exists |
| Student | `/api/student/applications/` | Own applications, statuses and interview information |
| Student | `/api/student/applications/<application_id>/job/` | Read-only details for the signed-in student's own application, even after the listing closes or expires |
| Company | `/api/company/profile/` | Own profile (including any saved logo URL) in `profile`, or `null` if no profile exists |
| Student or company | `/api/profile/picture/` | Signed-in account's own photo or logo; never returns another account's image |
| Company | `/api/company/jobs/` and `/api/company/jobs/{id}/` | Own job listings and job edit-form data |
| Company | `/api/company/jobs/{id}/applicants/` | Applicants for the company's own job |
| Company | `/api/company/applications/{id}/` | Application review data, including a protected `cv_url` if present |
| Company | `/api/company/applications/{id}/cv/` | Protected PDF download; this route uses an application ID |

List endpoints return `{count, next, previous, results}`. In Angular, render `results`. Use relative URL requests under `/api/` and use `?page=2` for the next page, or take the path and query from the `next` URL. Job filters: `keyword`, `job_type`, `work_mode`, `location`, `skill` (ID), and `sort=deadline` (default: newest). Example: `/api/jobs/?job_type=part_time`. The Q&A list accepts `keyword`.

## Write endpoints

Angular calls `GET /api/auth/csrf/` first. Django issues the `csrftoken` cookie, which Angular sends in `X-CSRFToken` for same-origin `POST` requests. Angular sends HTML-compatible form data, including multipart CV uploads and repeated skill values. Auth uses the Django session cookie; no JWT is required.

| Action | POST path |
|---|---|
| Sign in, register or sign out | `/api/auth/login/`, `/api/auth/register/`, `/api/auth/logout/` |
| Save own profile | `/api/student/profile/save/`, `/api/company/profile/save/` |
| Apply for a job | `/api/jobs/{id}/apply/` |
| Create, edit or close a company listing | `/api/company/jobs/create/`, `/api/company/jobs/{id}/save/`, `/api/company/jobs/{id}/close/` |
| Update application status | `/api/company/applications/{id}/review/` |
| Create or edit a question | `/api/forum/questions/create/`, `/api/forum/questions/{id}/save/` |
| Post, edit or accept an answer | `/api/forum/questions/{id}/answer/`, `/api/forum/answers/{id}/save/`, `/api/forum/answers/{id}/accept/` |

Registration and both profile-save endpoints accept an optional multipart `profile_picture` file (JPG, PNG or WebP, up to 2 MB). Omitting it on edit keeps the current image. An image at signup does not complete the profile or change approval requirements.

The application and company review APIs enforce the same role, ownership and status rules as Django. New or edited listings require approval in Django Admin. Approval and forum moderation remain in Django Admin.

The Angular dev proxy forwards `/api/`, `/admin/` and Django static resources to Django on port 8000. The proxy is for local development. For production, serve Angular and Django under the same HTTPS origin and route those paths to Django, keeping sensitive uploads private. Do not disable CSRF or expose the media directory publicly.
