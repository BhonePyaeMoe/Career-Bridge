from django.contrib import admin
from .models import Company
from core.models import AuditLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["company_name", "user", "industry", "approval_status", "created_at"]
    list_filter = ["approval_status", "industry"]
    search_fields = ["company_name", "user__username", "user__email"]
    actions = ["approve_companies", "reject_companies"]

    @admin.action(description="Approve selected companies")
    def approve_companies(self, request, queryset):
        for company in queryset:
            company.approval_status = Company.ApprovalStatus.APPROVED
            company.save(update_fields=["approval_status"])
            AuditLog.objects.create(actor=request.user, action="company_approved", object_type="Company", object_id=str(company.pk))

    @admin.action(description="Reject selected companies")
    def reject_companies(self, request, queryset):
        for company in queryset:
            company.approval_status = Company.ApprovalStatus.REJECTED
            company.save(update_fields=["approval_status"])
            AuditLog.objects.create(actor=request.user, action="company_rejected", object_type="Company", object_id=str(company.pk))

# Register your models here.
