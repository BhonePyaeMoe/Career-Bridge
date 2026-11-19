import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import StudentProfile, User
from jobs.models import Job
from .forms import ApplicationForm, ApplicationStatusForm
from .models import Application
from core.models import AuditLog


@login_required
def apply(request, job_id):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    student = get_object_or_404(StudentProfile, user=request.user)
    if not student.profile_is_complete:
        messages.info(request, "Complete your student profile before applying.")
        return redirect("accounts:student_profile")
    job = get_object_or_404(Job, pk=job_id)
    if not job.is_open:
        messages.error(request, "This job is not open for applications.")
        return redirect("jobs:detail", pk=job.pk)
    if Application.objects.filter(student=student, job=job).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect("applications:student_list")

    form = ApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                locked_job = Job.objects.select_for_update().get(pk=job.pk)
                if not locked_job.is_open:
                    messages.error(request, "This job is no longer open.")
                    return redirect("jobs:detail", pk=job.pk)
                application = Application.objects.create(student=student, job=locked_job, cover_message=form.cleaned_data["cover_message"])
                AuditLog.objects.create(actor=request.user, action="application_submitted", object_type="Application", object_id=str(application.pk))
        except IntegrityError:
            messages.info(request, "You have already applied for this job.")
        else:
            messages.success(request, "Application submitted.")
        return redirect("applications:student_list")
    return render(request, "applications/apply.html", {"form": form, "job": job})


@login_required
def student_applications(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    student = get_object_or_404(StudentProfile, user=request.user)
    applications = student.applications.select_related("job", "job__company")
    return render(request, "applications/student_applications.html", {"applications": applications})


@login_required
def job_applicants(request, job_id):
    if request.user.role != User.Role.COMPANY:
        raise PermissionDenied
    job = get_object_or_404(Job, pk=job_id, company__user=request.user)
    applications = job.applications.select_related("student", "student__user")
    return render(request, "applications/job_applicants.html", {"job": job, "applications": applications})


@login_required
def update_status(request, pk):
    if request.user.role != User.Role.COMPANY:
        raise PermissionDenied
    application = get_object_or_404(Application, pk=pk, job__company__user=request.user)
    form = ApplicationStatusForm(request.POST or None, instance=application)
    if request.method == "POST" and form.is_valid():
        old_status = application.status
        form.save()
        AuditLog.objects.create(actor=request.user, action="application_status_changed", object_type="Application", object_id=str(application.pk), details=f"{old_status} -> {application.status}")
        messages.success(request, "Application status updated.")
        return redirect("applications:job_applicants", job_id=application.job_id)
    return render(request, "applications/update_status.html", {"form": form, "application": application})


@login_required
def download_cv(request, student_id):
    student = get_object_or_404(StudentProfile, pk=student_id)
    allowed = request.user.is_staff or request.user == student.user
    if request.user.role == User.Role.COMPANY:
        allowed = Application.objects.filter(student=student, job__company__user=request.user).exists()
    if not allowed:
        raise PermissionDenied
    if not student.cv:
        raise Http404("No CV uploaded.")
    return FileResponse(student.cv.open("rb"), as_attachment=True, filename=os.path.basename(student.cv.name))
