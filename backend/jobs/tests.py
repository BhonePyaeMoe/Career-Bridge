from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from companies.models import Company
from .models import Job


class JobSecurityTests(TestCase):
    def setUp(self):
        self.company_user = User.objects.create_user("company1", "c1@example.com", "Pass123!!", role="company")
        self.other_user = User.objects.create_user("company2", "c2@example.com", "Pass123!!", role="company")
        self.company = Company.objects.create(user=self.company_user, company_name="One Co", industry="IT", phone="1", description="x", address="x", approval_status="approved")
        self.other_company = Company.objects.create(user=self.other_user, company_name="Two Co", industry="IT", phone="2", description="x", address="x", approval_status="approved")
        self.job = Job.objects.create(company=self.company, title="Django Intern", description="x", requirements="x", job_type="internship", work_mode="remote", deadline=timezone.localdate()+timedelta(days=10), approval_status="approved")

    def test_only_approved_jobs_are_public(self):
        Job.objects.create(company=self.company, title="Hidden Job", description="x", requirements="x", job_type="internship", work_mode="remote", deadline=timezone.localdate()+timedelta(days=10), approval_status="pending")
        response = self.client.get(reverse("jobs:list"))
        self.assertContains(response, "Django Intern")
        self.assertNotContains(response, "Hidden Job")

    def test_company_cannot_edit_another_company_job(self):
        self.client.force_login(self.other_user)
        response = self.client.get(reverse("jobs:edit", args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)

# Create your tests here.
