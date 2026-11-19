from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["student", "job", "status", "applied_at"]
    list_filter = ["status", "applied_at"]
    search_fields = ["student__full_name", "job__title", "job__company__company_name"]
    readonly_fields = ["student", "job", "applied_at"]

# Register your models here.
