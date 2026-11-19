from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.models import StudentProfile, User
from applications.forms import ApplicationForm, ApplicationStatusForm
from applications.models import Application
from companies.models import Company
from core.models import AuditLog
from forum.forms import AnswerForm, QuestionForm
from forum.models import Answer, Question
from jobs.forms import JobForm
from jobs.models import Job
from .profile_pictures import ImageCompanyForm, ImageRegistrationForm, ImageStudentProfileForm
from .views import owned_applications, public_jobs, require_role


def errors(form):
    return {field: [entry['message'] for entry in entries]
            for field, entries in form.errors.get_json_data().items()}


def audit(user, action, obj):
    AuditLog.objects.create(actor=user, action=action, object_type=type(obj).__name__, object_id=str(obj.pk))


@require_GET
@never_cache
def csrf(request):
    get_token(request)
    return JsonResponse({'ready': True})


@require_POST
@csrf_protect
@never_cache
def sign_in(request):
    form = AuthenticationForm(request, data=request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': errors(form)}, status=400)
    login(request, form.get_user())
    return JsonResponse({'ok': True})


@require_POST
@csrf_protect
@never_cache
def register(request):
    if request.user.is_authenticated:
        return JsonResponse({'detail': 'Sign out before creating a new account.'}, status=400)
    form = ImageRegistrationForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'errors': errors(form)}, status=400)
    try:
        with transaction.atomic():
            user = form.save()
            audit(user, 'account_registered', user)
            if picture := form.cleaned_data['profile_picture']:
                model = StudentProfile if user.role == User.Role.STUDENT else Company
                model.objects.create(user=user, profile_picture=picture)
    except IntegrityError:
        return JsonResponse({'detail': 'An account already uses that username or email.'}, status=409)
    login(request, user)
    return JsonResponse({'ok': True}, status=201)


@require_POST
@csrf_protect
@never_cache
def sign_out(request):
    logout(request)
    return JsonResponse({'ok': True})


@api_view(['POST'])
@transaction.atomic
def save_student_profile(request):
    require_role(request, User.Role.STUDENT)
    User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
    profile = StudentProfile.objects.filter(user=request.user).first() or StudentProfile(user=request.user)
    old_picture = profile.profile_picture
    form = ImageStudentProfileForm(request.data, request.FILES, instance=profile)
    if not form.is_valid():
        return Response({'errors': errors(form)}, status=400)
    saved = form.save()
    retire_picture(old_picture, saved.profile_picture)
    return Response({'ok': True})


@api_view(['POST'])
@transaction.atomic
def save_company_profile(request):
    require_role(request, User.Role.COMPANY)
    User.objects.select_for_update(no_key=True).get(pk=request.user.pk)
    profile = Company.objects.select_for_update().filter(user=request.user).first() or Company(user=request.user)
    old_picture = profile.profile_picture
    form = ImageCompanyForm(request.data, request.FILES, instance=profile)
    if not form.is_valid():
        return Response({'errors': errors(form)}, status=400)
    saved = form.save()
    retire_picture(old_picture, saved.profile_picture)
    return Response({'ok': True})


def retire_picture(old, current):
    if old and old.name != current.name:
        transaction.on_commit(lambda: old.storage.delete(old.name), robust=True)


@api_view(['POST'])
@transaction.atomic
def save_job(request, pk=None):
    require_role(request, User.Role.COMPANY)
    company = get_object_or_404(Company.objects.select_for_update(), user=request.user)
    if not company.is_approved:
        raise PermissionDenied('An administrator must approve your company first.')
    job = get_object_or_404(Job.objects.select_for_update(), pk=pk, company=company) if pk is not None else Job(company=company)
    form = JobForm(request.data, instance=job)
    if not form.is_valid():
        return Response({'errors': errors(form)}, status=400)
    job = form.save(commit=False)
    job.approval_status = Job.ApprovalStatus.PENDING
    job.save()
    form.save_m2m()
    audit(request.user, 'job_edited' if pk is not None else 'job_created', job)
    return Response({'id': job.pk}, status=200 if pk is not None else 201)


@api_view(['POST'])
@transaction.atomic
def close_job(request, pk):
    require_role(request, User.Role.COMPANY)
    job = get_object_or_404(Job.objects.select_for_update(), pk=pk, company__user=request.user)
    job.approval_status = Job.ApprovalStatus.CLOSED
    job.save(update_fields=['approval_status', 'updated_at'])
    audit(request.user, 'job_closed', job)
    return Response({'ok': True})


@api_view(['POST'])
def apply(request, pk):
    require_role(request, User.Role.STUDENT)
    student = StudentProfile.objects.filter(user=request.user).first()
    if student is None or not student.profile_is_complete:
        return Response({'detail': 'Complete your student profile before applying.'}, status=400)
    form = ApplicationForm(request.data)
    if not form.is_valid():
        return Response({'errors': errors(form)}, status=400)
    with transaction.atomic():
        job = get_object_or_404(public_jobs().select_for_update(), pk=pk)
        application, created = Application.objects.get_or_create(
            student=student, job=job, defaults={'cover_message': form.cleaned_data['cover_message']},
        )
        if not created:
            return Response({'detail': 'You already applied to this job.'}, status=409)
        audit(request.user, 'application_submitted', application)
    return Response({'id': application.pk}, status=201)


@api_view(['POST'])
@transaction.atomic
def review(request, pk):
    application = get_object_or_404(owned_applications(request).select_for_update(), pk=pk)
    form = ApplicationStatusForm(request.data, instance=application)
    if not form.is_valid():
        return Response({'errors': errors(form)}, status=400)
    audit(request.user, 'application_status_changed', form.save())
    return Response({'ok': True})


@api_view(['POST'])
@transaction.atomic
def save_question(request, pk=None):
    question = (get_object_or_404(Question.objects.select_for_update(), pk=pk, author=request.user, is_visible=True)
                if pk is not None else Question(author=request.user))
    form = QuestionForm(request.data, instance=question)
    if not form.is_valid():
        return Response({'errors': errors(form)}, status=400)
    question = form.save()
    audit(request.user, 'question_edited' if pk is not None else 'question_created', question)
    return Response({'id': question.pk}, status=200 if pk is not None else 201)


@api_view(['POST'])
@transaction.atomic
def save_answer(request, question_id=None, pk=None):
    if pk is not None:
        answer = get_object_or_404(Answer.objects.select_for_update(), pk=pk, author=request.user,
                                   is_visible=True, question__is_visible=True)
    else:
        question = get_object_or_404(Question.objects.select_for_update(), pk=question_id, is_visible=True)
        answer = Answer(author=request.user, question=question)
    form = AnswerForm(request.data, instance=answer)
    if not form.is_valid():
        return Response({'errors': errors(form)}, status=400)
    answer = form.save()
    audit(request.user, 'answer_edited' if pk is not None else 'answer_created', answer)
    return Response({'id': answer.pk}, status=200 if pk is not None else 201)


@api_view(['POST'])
@transaction.atomic
def accept_answer(request, pk):
    question = get_object_or_404(Question.objects.select_for_update(), answers__pk=pk,
                                 author=request.user, is_visible=True)
    answer = get_object_or_404(Answer, pk=pk, question=question, is_visible=True)
    question.answers.filter(is_accepted=True).exclude(pk=pk).update(is_accepted=False)
    answer.is_accepted = True
    answer.save(update_fields=['is_accepted', 'updated_at'])
    audit(request.user, 'answer_accepted', answer)
    return Response({'ok': True})
