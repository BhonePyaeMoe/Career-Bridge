from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from pathlib import Path
from uuid import uuid4


def validate_file_size(value):
    if value.size > 5 * 1024 * 1024:
        from django.core.exceptions import ValidationError
        raise ValidationError("CV file must be 5 MB or smaller.")


def cv_upload_path(instance, filename):
    return f"cvs/{instance.user_id}/{uuid4().hex}{Path(filename).suffix.lower()}"


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        COMPANY = "company", "Company"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    REQUIRED_FIELDS = ["email", "role"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    full_name = models.CharField(max_length=150)
    university = models.CharField(max_length=150)
    degree = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    cv = models.FileField(upload_to=cv_upload_path, blank=True, validators=[FileExtensionValidator(["pdf"]), validate_file_size])
    skills = models.ManyToManyField("jobs.Skill", blank=True, related_name="students")

    def __str__(self):
        return self.full_name

# Create your models here.
