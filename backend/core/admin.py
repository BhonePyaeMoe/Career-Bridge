from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "action", "object_type", "object_id"]
    list_filter = ["action", "object_type"]
    search_fields = ["actor__username", "action", "details"]
    readonly_fields = ["actor", "action", "object_type", "object_id", "details", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Register your models here.
