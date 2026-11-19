from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["title", "description", "requirements", "job_type", "work_mode", "location", "deadline", "skills"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "skills": forms.CheckboxSelectMultiple(),
        }
