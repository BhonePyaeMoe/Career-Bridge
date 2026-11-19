from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StudentProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "is_active", "is_staff"]
    list_filter = ["role", "is_active", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (("CareerBridge", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("CareerBridge", {"fields": ("email", "role")}),)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    exclude = ("profile_picture",)
    list_display = ["full_name", "user", "university", "degree"]
    search_fields = ["full_name", "user__username", "university"]

# Register your models here.
