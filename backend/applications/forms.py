from django import forms
from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_message"]
        widgets = {"cover_message": forms.Textarea(attrs={"rows": 5})}


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status", "interview_datetime", "interview_location", "company_message"]
        widgets = {"interview_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["interview_datetime"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_status(self):
        new_status = self.cleaned_data["status"]
        current = self.instance.status
        allowed = {
            Application.Status.APPLIED: {Application.Status.UNDER_REVIEW, Application.Status.NOT_SELECTED},
            Application.Status.UNDER_REVIEW: {Application.Status.INTERVIEW_APPROVED, Application.Status.NOT_SELECTED},
            Application.Status.INTERVIEW_APPROVED: set(),
            Application.Status.NOT_SELECTED: set(),
        }
        if new_status != current and new_status not in allowed[current]:
            raise forms.ValidationError("This status change is not allowed.")
        return new_status
