from django.db.models import BooleanField, Count, Exists, F, OuterRef, Prefetch, Q, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.forms import UNIVERSITY_CHOICES
from accounts.models import StudentProfile, User
from applications.models import Application
from companies.models import Company
from forum.models import Answer, Question
from jobs.models import Job, JobBookmark, Skill
from . import serializers as data


class ListPagination(PageNumberPagination):
    page_size = 20


def listing(request, queryset, serializer):
    pager = ListPagination()
    page = pager.paginate_queryset(queryset, request)
    return pager.get_paginated_response(serializer(page, many=True).data)


def require_role(request, role):
    if request.user.role != role:
        raise PermissionDenied('This page is not available for your account role.')


def jobs_with_details():
    return Job.objects.select_related('company').prefetch_related('skills')


def public_jobs():
    return jobs_with_details().filter(
        approval_status=Job.ApprovalStatus.APPROVED,
        company__approval_status=Company.ApprovalStatus.APPROVED,
        deadline__gte=timezone.localdate(),
    )


def with_bookmark_state(queryset, user):
    bookmarked = Value(False, output_field=BooleanField())
    if user.is_authenticated and user.role == User.Role.STUDENT:
        bookmarked = Exists(JobBookmark.objects.filter(student=user, job_id=OuterRef('pk')))
    return queryset.annotate(bookmarked=bookmarked)


@never_cache
@api_view(['GET'])
@permission_classes([AllowAny])
def job_list(request):
    queryset = with_bookmark_state(public_jobs(), request.user)
    params = request.query_params
    keyword = params.get('keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword)
            | Q(company__company_name__icontains=keyword) | Q(skills__name__icontains=keyword)
        ).distinct()
    for field in ('job_type', 'work_mode'):
        if params.get(field):
            queryset = queryset.filter(**{field: params[field]})
    if params.get('location'):
        queryset = queryset.filter(location__icontains=params['location'].strip())
    if params.get('skill'):
        raw_skill = params['skill']
        if not raw_skill.isascii() or not raw_skill.isdecimal() or len(raw_skill) > 18 or int(raw_skill) < 1:
            raise ValidationError({'skill': 'Enter a valid skill ID.'})
        queryset = queryset.filter(skills__id=int(raw_skill))
    sort = 'deadline' if params.get('sort') == 'deadline' else '-created_at'
    return listing(request, queryset.order_by(sort, 'pk'), data.PublicJobSerializer)


@never_cache
@api_view(['GET'])
@permission_classes([AllowAny])
def job_detail(request, pk):
    job = get_object_or_404(with_bookmark_state(public_jobs(), request.user), pk=pk)
    job.already_applied = (
        request.user.is_authenticated and request.user.role == User.Role.STUDENT
        and job.applications.filter(student__user=request.user).exists()
    )
    return Response(data.PublicJobDetailSerializer(job).data)


@never_cache
@api_view(['GET'])
def saved_jobs(request):
    require_role(request, User.Role.STUDENT)
    queryset = jobs_with_details().filter(bookmarks__student=request.user).annotate(
        available=Exists(public_jobs().filter(pk=OuterRef('pk'))),
        saved_title=F('bookmarks__job_title'),
    ).order_by('-bookmarks__created_at', 'pk')
    return listing(request, queryset, data.SavedJobSerializer)


@api_view(['GET'])
@permission_classes([AllowAny])
def options(request):
    return Response({
        'skills': data.SkillSerializer(Skill.objects.all(), many=True).data,
        'job_types': [{'value': value, 'label': label} for value, label in Job.JobType.choices],
        'work_modes': [{'value': value, 'label': label} for value, label in Job.WorkMode.choices],
        'universities': [{'value': value, 'label': label} for value, label in UNIVERSITY_CHOICES],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def session(request):
    user = request.user
    if not user.is_authenticated:
        return Response({'authenticated': False, 'user': None}, headers={'Cache-Control': 'no-store'})
    return Response({'authenticated': True, 'user': {
        'id': user.pk, 'username': user.username, 'role': user.role,
    }}, headers={'Cache-Control': 'no-store'})


@api_view(['GET'])
def student_profile(request):
    require_role(request, User.Role.STUDENT)
    profile = StudentProfile.objects.prefetch_related('skills').filter(user=request.user).first()
    return Response({'profile': data.StudentProfileSerializer(profile).data if profile else None})


@api_view(['GET'])
def company_profile(request):
    require_role(request, User.Role.COMPANY)
    profile = Company.objects.filter(user=request.user).first()
    return Response({'profile': data.CompanyProfileSerializer(profile).data if profile else None})


@never_cache
@api_view(['GET'])
def own_profile_picture(request):
    if request.user.role == User.Role.STUDENT:
        model = StudentProfile
    elif request.user.role == User.Role.COMPANY:
        model = Company
    else:
        raise PermissionDenied()
    picture = get_object_or_404(model, user=request.user).profile_picture
    if not picture or not picture.name.endswith('.webp'):
        raise NotFound('No profile image available.')
    try:
        response = FileResponse(picture.open('rb'), content_type='image/webp')
    except FileNotFoundError as exc:
        raise NotFound('The profile image is unavailable.') from exc
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@api_view(['GET'])
def student_applications(request):
    require_role(request, User.Role.STUDENT)
    queryset = Application.objects.filter(student__user=request.user).select_related('job__company')
    return listing(request, queryset.order_by('-applied_at', 'pk'), data.ApplicationSerializer)


@api_view(['GET'])
def company_jobs(request, job_id=None):
    require_role(request, User.Role.COMPANY)
    queryset = jobs_with_details().filter(company__user=request.user)
    if job_id is not None:
        return Response(data.CompanyJobSerializer(get_object_or_404(queryset, pk=job_id)).data)
    return listing(request, queryset.order_by('-created_at', 'pk'), data.CompanyJobSerializer)


def owned_applications(request):
    require_role(request, User.Role.COMPANY)
    return Application.objects.filter(job__company__user=request.user).select_related('job__company', 'student')


@api_view(['GET'])
def job_applicants(request, job_id):
    queryset = owned_applications(request)
    job = get_object_or_404(Job, pk=job_id, company__user=request.user)
    return listing(request, queryset.filter(job=job).order_by('-applied_at', 'pk'), data.ApplicantSerializer)


@api_view(['GET'])
def application_review(request, pk):
    application = get_object_or_404(owned_applications(request), pk=pk)
    return Response(data.ApplicantSerializer(application).data)


@api_view(['GET'])
def applicant_cv(request, pk):
    application = get_object_or_404(owned_applications(request), pk=pk)
    cv = application.student.cv
    if not cv:
        raise NotFound('No CV uploaded.')
    try:
        file = cv.open('rb')
    except FileNotFoundError as exc:
        raise NotFound('The CV file is unavailable.') from exc
    response = FileResponse(file, as_attachment=True, filename='cv.pdf', content_type='application/pdf')
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def visible_questions():
    return Question.objects.filter(is_visible=True).select_related('author').annotate(
        answer_count=Count('answers', filter=Q(answers__is_visible=True))
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def question_list(request):
    queryset = visible_questions()
    keyword = request.query_params.get('keyword', '').strip()
    if keyword:
        queryset = queryset.filter(Q(title__icontains=keyword) | Q(body__icontains=keyword))
    return listing(request, queryset.order_by('-created_at', 'pk'), data.QuestionSerializer)


@api_view(['GET'])
@permission_classes([AllowAny])
def question_detail(request, pk):
    answers = Answer.objects.filter(is_visible=True).select_related('author')
    queryset = visible_questions().prefetch_related(Prefetch('answers', queryset=answers, to_attr='visible_answers'))
    return Response(data.QuestionDetailSerializer(get_object_or_404(queryset, pk=pk)).data)
