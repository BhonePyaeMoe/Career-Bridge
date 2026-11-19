from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import UploadedFile
from .models import StudentProfile, User


THAI_UNIVERSITIES = [
    "Asian Institute of Technology",
    "Assumption University",
    "Bangkok University",
    "Burapha University",
    "Chiang Mai University",
    "Chulalongkorn University",
    "Dhurakij Pundit University",
    "Huachiew Chalermprakiet University",
    "Kasetsart University",
    "Khon Kaen University",
    "King Mongkut's Institute of Technology Ladkrabang",
    "King Mongkut's University of Technology North Bangkok",
    "King Mongkut's University of Technology Thonburi",
    "Mae Fah Luang University",
    "Maejo University",
    "Mahasarakham University",
    "Mahidol University",
    "Naresuan University",
    "National Institute of Development Administration",
    "Payap University",
    "Prince of Songkla University",
    "Rangsit University",
    "Silpakorn University",
    "Srinakharinwirot University",
    "Sripatum University",
    "Suranaree University of Technology",
    "Thammasat University",
    "University of the Thai Chamber of Commerce",
    "Walailak University",
]

UNIVERSITY_CHOICES = [("", "Select your university")]
UNIVERSITY_CHOICES += [(name, name) for name in THAI_UNIVERSITIES]
UNIVERSITY_CHOICES += [("__other__", "Other university (not listed)")]


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=[(User.Role.STUDENT, "Student"), (User.Role.COMPANY, "Company")])

    class Meta:
        model = User
        fields = ["username", "email", "role", "password1", "password2"]


class StudentProfileForm(forms.ModelForm):
    university = forms.ChoiceField(choices=UNIVERSITY_CHOICES)
    other_university = forms.CharField(
        required=False,
        label="University name",
        widget=forms.TextInput(attrs={"placeholder": "Enter your university name"}),
    )

    class Meta:
        model = StudentProfile
        fields = ["full_name", "university", "other_university", "degree", "phone", "bio", "cv", "skills"]
        widgets = {"skills": forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.university:
            if self.instance.university in THAI_UNIVERSITIES:
                self.initial["university"] = self.instance.university
            else:
                self.initial["university"] = "__other__"
                self.initial["other_university"] = self.instance.university

    def clean(self):
        cleaned_data = super().clean()
        university = cleaned_data.get("university")
        other_university = cleaned_data.get("other_university", "").strip()
        if university == "__other__" and not other_university:
            self.add_error("other_university", "Enter your university name.")
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        selected = self.cleaned_data["university"]
        profile.university = self.cleaned_data["other_university"].strip() if selected == "__other__" else selected
        if commit:
            profile.save()
            self.save_m2m()
        return profile

    def clean_cv(self):
        cv = self.cleaned_data.get("cv")
        if isinstance(cv, UploadedFile):
            if getattr(cv, "content_type", "application/pdf") != "application/pdf":
                raise forms.ValidationError("Only PDF files are allowed.")
            header = cv.read(5)
            cv.seek(0)
            if header != b"%PDF-":
                raise forms.ValidationError("The uploaded file is not a valid PDF.")
        return cv
