from django.contrib import admin
from .models import Job, Skill
from core.models import AuditLog


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "job_type", "deadline", "approval_status"]
    list_filter = ["approval_status", "job_type", "work_mode"]
    search_fields = ["title", "company__company_name"]
    filter_horizontal = ["skills"]
    actions = ["approve_jobs", "reject_jobs"]

    @admin.action(description="Approve selected jobs")
    def approve_jobs(self, request, queryset):
        for job in queryset:
            job.approval_status = Job.ApprovalStatus.APPROVED
            job.save(update_fields=["approval_status"])
            AuditLog.objects.create(actor=request.user, action="job_approved", object_type="Job", object_id=str(job.pk))

    @admin.action(description="Reject selected jobs")
    def reject_jobs(self, request, queryset):
        for job in queryset:
            job.approval_status = Job.ApprovalStatus.REJECTED
            job.save(update_fields=["approval_status"])
            AuditLog.objects.create(actor=request.user, action="job_rejected", object_type="Job", object_id=str(job.pk))

# Register your models here.
