from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from .models import Answer, Question


class ForumTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("student", "student@example.com", "StrongPass123!", role="student")
        self.company = User.objects.create_user("company", "company@example.com", "StrongPass123!", role="company")
        self.other = User.objects.create_user("other", "other@example.com", "StrongPass123!", role="student")
        self.question = Question.objects.create(author=self.student, title="Interview preparation", body="How should I prepare?")

    def test_logged_in_user_can_create_question(self):
        self.client.force_login(self.company)
        response = self.client.post(reverse("forum:create"), {"title": "Internship CV", "body": "What should a CV contain?"})
        question = Question.objects.get(title="Internship CV")
        self.assertRedirects(response, reverse("forum:detail", args=[question.pk]))
        self.assertEqual(question.author, self.company)

    def test_anonymous_user_cannot_create_question(self):
        response = self.client.get(reverse("forum:create"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('forum:create')}")

    def test_hidden_question_is_not_public(self):
        self.question.is_visible = False
        self.question.save(update_fields=["is_visible"])
        response = self.client.get(reverse("forum:list"))
        self.assertNotContains(response, self.question.title)
        self.assertEqual(self.client.get(reverse("forum:detail", args=[self.question.pk])).status_code, 404)

    def test_user_cannot_edit_another_users_question(self):
        self.client.force_login(self.company)
        response = self.client.get(reverse("forum:edit", args=[self.question.pk]))
        self.assertEqual(response.status_code, 404)

    def test_company_can_answer_student_question(self):
        self.client.force_login(self.company)
        response = self.client.post(reverse("forum:answer_create", args=[self.question.pk]), {"body": "Review the job requirements."})
        self.assertRedirects(response, reverse("forum:detail", args=[self.question.pk]))
        self.assertTrue(Answer.objects.filter(question=self.question, author=self.company).exists())

    def test_question_author_can_accept_only_one_answer(self):
        first = Answer.objects.create(question=self.question, author=self.company, body="First")
        second = Answer.objects.create(question=self.question, author=self.other, body="Second")
        self.client.force_login(self.student)
        self.client.post(reverse("forum:accept_answer", args=[first.pk]))
        self.client.post(reverse("forum:accept_answer", args=[second.pk]))
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_accepted)
        self.assertTrue(second.is_accepted)

    def test_non_author_cannot_accept_answer(self):
        answer = Answer.objects.create(question=self.question, author=self.company, body="Answer")
        self.client.force_login(self.other)
        response = self.client.post(reverse("forum:accept_answer", args=[answer.pk]))
        self.assertEqual(response.status_code, 403)

# Create your tests here.
