from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.job_list, name="list"),
    path("company/", views.company_jobs, name="company_jobs"),
    path("create/", views.job_create, name="create"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("<int:pk>/edit/", views.job_edit, name="edit"),
    path("<int:pk>/close/", views.job_close, name="close"),
]
