from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import StudentProfile
from jobs.models import Job


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        UNDER_REVIEW = "under_review", "Under Review"
        INTERVIEW_APPROVED = "interview_approved", "Interview Approved"
        NOT_SELECTED = "not_selected", "Not Selected"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    cover_message = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    interview_datetime = models.DateTimeField(blank=True, null=True)
    interview_location = models.CharField(max_length=255, blank=True)
    company_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [models.UniqueConstraint(fields=["student", "job"], name="unique_student_job_application")]

    def clean(self):
        if self.status == self.Status.INTERVIEW_APPROVED:
            if not self.interview_datetime:
                raise ValidationError({"interview_datetime": "Interview date and time are required."})
            if not self.interview_location.strip():
                raise ValidationError({"interview_location": "Interview location or meeting link is required."})

    def __str__(self):
        return f"{self.student.full_name} - {self.job.title}"

# Create your models here.
