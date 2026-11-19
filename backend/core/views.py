from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from accounts.models import User


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin:index")
    if request.user.role == User.Role.STUDENT:
        if not hasattr(request.user, "student_profile") or not request.user.student_profile.full_name:
            return redirect("accounts:student_profile")
        return render(request, "core/student_dashboard.html")
    if request.user.role == User.Role.COMPANY:
        if not hasattr(request.user, "company_profile") or not request.user.company_profile.company_name:
            return redirect("companies:profile")
        return render(request, "core/company_dashboard.html", {"company": request.user.company_profile})
    return render(request, "core/home.html")
