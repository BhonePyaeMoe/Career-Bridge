from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("student-profile/", views.student_profile, name="student_profile"),
]
