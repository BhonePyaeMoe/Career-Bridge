from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.models import User
from companies.models import Company
from .forms import JobForm
from .models import Job, Skill
from core.models import AuditLog


def job_list(request):
    jobs = Job.objects.select_related("company").prefetch_related("skills").filter(
        approval_status=Job.ApprovalStatus.APPROVED,
        deadline__gte=timezone.localdate(),
    )
    keyword = request.GET.get("keyword", "").strip()
    job_type = request.GET.get("job_type", "")
    work_mode = request.GET.get("work_mode", "")
    location = request.GET.get("location", "").strip()
    skill = request.GET.get("skill", "")
    sort = request.GET.get("sort", "newest")

    if keyword:
        jobs = jobs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(company__company_name__icontains=keyword) | Q(skills__name__icontains=keyword))
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if work_mode:
        jobs = jobs.filter(work_mode=work_mode)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if skill:
        jobs = jobs.filter(skills__id=skill)
    jobs = jobs.distinct().order_by("deadline" if sort == "deadline" else "-created_at")

    page_obj = Paginator(jobs, 6).get_page(request.GET.get("page"))
    return render(request, "jobs/job_list.html", {
        "page_obj": page_obj,
        "skills": Skill.objects.all(),
        "job_types": Job.JobType.choices,
        "work_modes": Job.WorkMode.choices,
    })


def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related("company").prefetch_related("skills"), pk=pk, approval_status=Job.ApprovalStatus.APPROVED)
    already_applied = False
    if request.user.is_authenticated and request.user.role == User.Role.STUDENT and hasattr(request.user, "student_profile"):
        already_applied = job.applications.filter(student=request.user.student_profile).exists()
    return render(request, "jobs/job_detail.html", {"job": job, "already_applied": already_applied})


def _approved_company(user):
    if user.role != User.Role.COMPANY:
        raise PermissionDenied
    company = get_object_or_404(Company, user=user)
    if not company.is_approved:
        raise PermissionDenied("Your company must be approved first.")
    return company


@login_required
def company_jobs(request):
    if request.user.role != User.Role.COMPANY:
        raise PermissionDenied
    company = get_object_or_404(Company, user=request.user)
    return render(request, "jobs/company_jobs.html", {"company": company, "jobs": company.jobs.prefetch_related("skills")})


@login_required
def job_create(request):
    company = _approved_company(request.user)
    form = JobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.company = company
        job.approval_status = Job.ApprovalStatus.PENDING
        job.save()
        form.save_m2m()
        AuditLog.objects.create(actor=request.user, action="job_created", object_type="Job", object_id=str(job.pk))
        messages.success(request, "Job submitted for administrator approval.")
        return redirect("jobs:company_jobs")
    return render(request, "jobs/job_form.html", {"form": form, "heading": "Create job"})


@login_required
def job_edit(request, pk):
    company = _approved_company(request.user)
    job = get_object_or_404(Job, pk=pk, company=company)
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.approval_status = Job.ApprovalStatus.PENDING
        job.save()
        form.save_m2m()
        AuditLog.objects.create(actor=request.user, action="job_edited", object_type="Job", object_id=str(job.pk))
        messages.success(request, "Job updated and returned for administrator approval.")
        return redirect("jobs:company_jobs")
    return render(request, "jobs/job_form.html", {"form": form, "heading": "Edit job"})


@login_required
def job_close(request, pk):
    company = _approved_company(request.user)
    job = get_object_or_404(Job, pk=pk, company=company)
    if request.method == "POST":
        job.approval_status = Job.ApprovalStatus.CLOSED
        job.save(update_fields=["approval_status"])
        AuditLog.objects.create(actor=request.user, action="job_closed", object_type="Job", object_id=str(job.pk))
        messages.success(request, "Job closed.")
    return redirect("jobs:company_jobs")
