from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from .forms import RegistrationForm, StudentProfileForm
from .models import StudentProfile, User
from core.models import AuditLog


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        AuditLog.objects.create(actor=user, action="account_registered", object_type="User", object_id=str(user.pk), details=f"Role: {user.role}")
        login(request, user)
        messages.success(request, "Account created. Please complete your profile.")
        if user.role == User.Role.STUDENT:
            return redirect("accounts:student_profile")
        return redirect("companies:profile")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def student_profile(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    form = StudentProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student profile saved.")
        return redirect("core:dashboard")
    return render(request, "accounts/student_profile.html", {"form": form, "profile": profile})
