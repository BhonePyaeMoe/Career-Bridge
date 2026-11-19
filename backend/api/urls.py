from django.urls import path
from . import actions, views

app_name = 'api'

urlpatterns = [
    path('auth/csrf/', actions.csrf, name='csrf'),
    path('auth/login/', actions.sign_in, name='sign-in'),
    path('auth/register/', actions.register, name='register'),
    path('auth/logout/', actions.sign_out, name='sign-out'),
    path('student/profile/save/', actions.save_student_profile, name='student-profile-save'),
    path('company/profile/save/', actions.save_company_profile, name='company-profile-save'),
    path('jobs/<int:pk>/apply/', actions.apply, name='apply'),
    path('company/jobs/create/', actions.save_job, name='company-job-create'),
    path('company/jobs/<int:pk>/save/', actions.save_job, name='company-job-save'),
    path('company/jobs/<int:pk>/close/', actions.close_job, name='company-job-close'),
    path('company/applications/<int:pk>/review/', actions.review, name='review'),
    path('forum/questions/create/', actions.save_question, name='question-create'),
    path('forum/questions/<int:pk>/save/', actions.save_question, name='question-save'),
    path('forum/questions/<int:question_id>/answer/', actions.save_answer, name='answer-create'),
    path('forum/answers/<int:pk>/save/', actions.save_answer, name='answer-save'),
    path('forum/answers/<int:pk>/accept/', actions.accept_answer, name='answer-accept'),
    path('auth/session/', views.session, name='session'),
    path('options/', views.options, name='options'),
    path('jobs/', views.job_list, name='job-list'),
    path('jobs/<int:pk>/', views.job_detail, name='job-detail'),
    path('forum/questions/', views.question_list, name='question-list'),
    path('forum/questions/<int:pk>/', views.question_detail, name='question-detail'),
    path('student/profile/', views.student_profile, name='student-profile'),
    path('student/applications/', views.student_applications, name='student-applications'),
    path('company/profile/', views.company_profile, name='company-profile'),
    path('company/jobs/', views.company_jobs, name='company-jobs'),
    path('company/jobs/<int:job_id>/', views.company_jobs, name='company-job'),
    path('company/jobs/<int:job_id>/applicants/', views.job_applicants, name='job-applicants'),
    path('company/applications/<int:pk>/', views.application_review, name='application-review'),
    path('company/applications/<int:pk>/cv/', views.applicant_cv, name='applicant-cv'),
]
