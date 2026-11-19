from django.db import models
from django.conf import settings


class Company(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_profile")
    company_name = models.CharField(max_length=150)
    industry = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30)
    description = models.TextField()
    address = models.TextField()
    approval_status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_approved(self):
        return self.approval_status == self.ApprovalStatus.APPROVED

    def __str__(self):
        return self.company_name

# Create your models here.
