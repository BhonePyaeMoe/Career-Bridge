from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from companies.models import Company


class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Job(models.Model):
    class JobType(models.TextChoices):
        INTERNSHIP = "internship", "Internship"
        PART_TIME = "part_time", "Part-time"
        FULL_TIME = "full_time", "Full-time"

    class WorkMode(models.TextChoices):
        ONSITE = "onsite", "On-site"
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CLOSED = "closed", "Closed"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="jobs")
    title = models.CharField(max_length=150)
    description = models.TextField()
    requirements = models.TextField()
    job_type = models.CharField(max_length=20, choices=JobType.choices)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices)
    location = models.CharField(max_length=150, blank=True)
    deadline = models.DateField()
    approval_status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    skills = models.ManyToManyField(Skill, blank=True, related_name="jobs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.deadline and self.deadline < timezone.localdate():
            raise ValidationError({"deadline": "Deadline cannot be in the past."})
        if self.work_mode != self.WorkMode.REMOTE and not self.location.strip():
            raise ValidationError({"location": "Location is required for on-site and hybrid jobs."})

    @property
    def is_open(self):
        return self.approval_status == self.ApprovalStatus.APPROVED and self.deadline >= timezone.localdate()

    def __str__(self):
        return f"{self.title} - {self.company.company_name}"

class JobBookmark(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_bookmarks")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="bookmarks")
    job_title = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("student", "job"), name="unique_student_job_bookmark"),
        ]
