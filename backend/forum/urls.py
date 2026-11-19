from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.question_list, name="list"),
    path("ask/", views.question_create, name="create"),
    path("<int:pk>/", views.question_detail, name="detail"),
    path("<int:pk>/edit/", views.question_edit, name="edit"),
    path("<int:question_id>/answer/", views.answer_create, name="answer_create"),
    path("answer/<int:pk>/edit/", views.answer_edit, name="answer_edit"),
    path("answer/<int:pk>/accept/", views.accept_answer, name="accept_answer"),
]
