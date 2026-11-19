from django.test import TestCase
from django.urls import reverse
from .forms import StudentProfileForm
from .models import StudentProfile, User


class RegistrationTests(TestCase):
    def test_student_registration(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "student1", "email": "student@example.com", "role": "student",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertRedirects(response, reverse("accounts:student_profile"))
        self.assertEqual(User.objects.get(username="student1").role, User.Role.STUDENT)

    def test_public_registration_cannot_create_admin(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "fakeadmin", "email": "fake@example.com", "role": "admin",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="fakeadmin").exists())


class StudentProfileFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("student", "student@example.com", "StrongPass123!", role="student")
        self.profile = StudentProfile(user=self.user)

    def test_listed_university_is_saved(self):
        form = StudentProfileForm({
            "full_name": "Student One", "university": "Asian Institute of Technology",
            "other_university": "", "degree": "Computer Science", "phone": "", "bio": "",
        }, instance=self.profile)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().university, "Asian Institute of Technology")

    def test_other_university_requires_name(self):
        form = StudentProfileForm({
            "full_name": "Student One", "university": "__other__",
            "other_university": "", "degree": "Computer Science", "phone": "", "bio": "",
        }, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn("other_university", form.errors)

# Create your tests here.
