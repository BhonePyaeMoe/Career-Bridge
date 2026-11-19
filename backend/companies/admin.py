from django.contrib import admin
from django.contrib import messages
from .models import Company
from core.models import AuditLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    exclude = ("profile_picture",)
    list_display = ["company_name", "user", "industry", "approval_status", "created_at"]
    list_filter = ["approval_status", "industry"]
    search_fields = ["company_name", "user__username", "user__email"]
    actions = ["approve_companies", "reject_companies"]

    @admin.action(description="Approve selected companies")
    def approve_companies(self, request, queryset):
        for company in queryset:
            if not all((company.company_name, company.industry, company.phone, company.description, company.address)):
                self.message_user(request, "An incomplete company profile was skipped.", messages.WARNING)
                continue
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
