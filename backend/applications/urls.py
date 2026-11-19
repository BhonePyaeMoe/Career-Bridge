from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("apply/<int:job_id>/", views.apply, name="apply"),
    path("mine/", views.student_applications, name="student_list"),
    path("job/<int:job_id>/", views.job_applicants, name="job_applicants"),
    path("<int:pk>/status/", views.update_status, name="update_status"),
    path("cv/<int:student_id>/", views.download_cv, name="download_cv"),
]
