from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from accounts.models import User
from .forms import CompanyForm
from .models import Company


@login_required
def company_profile(request):
    if request.user.role != User.Role.COMPANY:
        raise PermissionDenied
    company, _ = Company.objects.get_or_create(user=request.user)
    form = CompanyForm(request.POST or None, instance=company)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Company profile saved and awaiting administrator approval.")
        return redirect("core:dashboard")
    return render(request, "companies/company_profile.html", {"form": form, "company": company})
