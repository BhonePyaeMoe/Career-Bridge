from datetime import timedelta
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import StudentProfile, User
from companies.models import Company
from jobs.models import Job
from .models import Application


class ApplicationTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user("student", "s@example.com", "Pass123!!", role="student")
        self.student = StudentProfile.objects.create(user=self.student_user, full_name="Student One", university="AIT", degree="CS")
        self.company_user = User.objects.create_user("company", "c@example.com", "Pass123!!", role="company")
        self.company = Company.objects.create(user=self.company_user, company_name="Tech Co", industry="IT", phone="1", description="x", address="x", approval_status="approved")
        self.job = Job.objects.create(company=self.company, title="Intern", description="x", requirements="x", job_type="internship", work_mode="remote", deadline=timezone.localdate()+timedelta(days=10), approval_status="approved")

    def test_student_can_apply(self):
        self.client.force_login(self.student_user)
        response = self.client.post(reverse("applications:apply", args=[self.job.pk]), {"cover_message": "Hello"})
        self.assertRedirects(response, reverse("applications:student_list"))
        self.assertTrue(Application.objects.filter(student=self.student, job=self.job).exists())

    def test_database_prevents_duplicate_application(self):
        Application.objects.create(student=self.student, job=self.job)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Application.objects.create(student=self.student, job=self.job)

    def test_other_company_cannot_view_applicants(self):
        other_user = User.objects.create_user("other", "o@example.com", "Pass123!!", role="company")
        Company.objects.create(user=other_user, company_name="Other", industry="IT", phone="2", description="x", address="x", approval_status="approved")
        self.client.force_login(other_user)
        response = self.client.get(reverse("applications:job_applicants", args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)

# Create your tests here.
