from datetime import timedelta
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import StudentProfile, User
from applications.models import Application
from companies.models import Company
from forum.models import Answer, Question
from jobs.models import Job, Skill


class AngularWriteApiTests(TestCase):
    password = 'SeedOnly-Pass-461!'

    def setUp(self):
        self.browser = Client(enforce_csrf_checks=True)
        self.student = User.objects.create_user('student', 'student@example.test', self.password, role=User.Role.STUDENT)
        self.employer = User.objects.create_user('company', 'company@example.test', self.password, role=User.Role.COMPANY)
        self.company = Company.objects.create(user=self.employer, company_name='Example Company', approval_status='approved')

    def post(self, name, payload=None, *args):
        self.browser.get(reverse('api:csrf'))
        return self.browser.post(reverse(f'api:{name}', args=args), payload or {},
                                 HTTP_X_CSRFTOKEN=self.browser.cookies['csrftoken'].value)

    def sign_in(self, user):
        self.assertEqual(self.post('sign-in', {'username': user.username, 'password': self.password}).status_code, 200)

    def test_anonymous_login_registration_and_logout_require_csrf(self):
        for route in ['sign-in', 'register', 'sign-out']:
            self.assertEqual(self.browser.post(reverse(f'api:{route}')).status_code, 403)
        form = {'username': 'new_student', 'email': 'new@example.test', 'role': 'admin',
                'password1': self.password, 'password2': self.password}
        self.assertEqual(self.post('register', form).status_code, 400)
        self.assertEqual(self.post('register', form | {'role': 'student'}).status_code, 201)
        self.assertEqual(self.browser.get(reverse('api:session')).json()['user']['role'], 'student')
        self.assertEqual(self.post('sign-out').status_code, 200)
        self.assertFalse(self.browser.get(reverse('api:session')).json()['authenticated'])

    def test_student_can_update_profile_with_multipart_pdf_and_keep_it(self):
        self.sign_in(self.student)
        skill = Skill.objects.create(name='Django')
        form = {'full_name': 'Test Student', 'university': '__other__', 'other_university': 'Example University',
                'degree': 'Computing', 'skills': [skill.pk]}
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            pdf = SimpleUploadedFile('cv.pdf', b'%PDF-test document', content_type='application/pdf')
            response = self.post('student-profile-save', form | {'cv': pdf})
            self.assertEqual(response.status_code, 200, response.content)
            profile = StudentProfile.objects.get(user=self.student)
            self.assertEqual(profile.university, 'Example University')
            self.assertEqual(list(profile.skills.all()), [skill])
            self.assertTrue(profile.cv)
            response = self.post('student-profile-save', form | {'bio': 'Updated bio'})
            self.assertEqual(response.status_code, 200, response.content)
            profile.refresh_from_db()
            self.assertEqual(profile.bio, 'Updated bio')
            self.assertTrue(profile.cv)

    def test_company_create_then_student_apply_and_company_review(self):
        self.sign_in(self.employer)
        self.assertEqual(self.post('company-profile-save', {'company_name': 'Example Company', 'industry': 'IT',
                             'description': 'Example', 'phone': '0123456', 'address': 'Bangkok'}).status_code, 200)
        payload = {'title': 'Developer Intern', 'job_type': 'internship', 'work_mode': 'remote',
                   'description': 'Example', 'requirements': 'Python',
                   'deadline': str(timezone.localdate() + timedelta(days=10))}
        response = self.post('company-job-create', payload)
        self.assertEqual(response.status_code, 201, response.content)
        job = Job.objects.get(pk=response.json()['id'])
        self.assertEqual(job.approval_status, 'pending')
        self.assertEqual(self.browser.get(reverse('api:job-list')).json()['count'], 0)
        Job.objects.filter(pk=job.pk).update(approval_status='approved')  # Simulates admin approval.
        StudentProfile.objects.create(user=self.student, full_name='Test Student')
        self.sign_in(self.student)
        response = self.post('apply', {'cover_message': 'Interested'}, job.pk)
        self.assertEqual(response.status_code, 201, response.content)
        application_id = response.json()['id']
        self.assertEqual(self.post('apply', {}, job.pk).status_code, 409)
        self.assertEqual(self.post('review', {'status': 'under_review'}, application_id).status_code, 403)
        outsider = User.objects.create_user('othercompany', 'other@example.test', self.password, role=User.Role.COMPANY)
        self.sign_in(outsider)
        self.assertEqual(self.post('review', {'status': 'under_review'}, application_id).status_code, 404)
        self.sign_in(self.employer)
        self.assertEqual(self.post('review', {'status': 'interview_approved'}, application_id).status_code, 400)
        result = self.post('review', {'status': 'under_review', 'company_message': 'We received your application.'}, application_id)
        self.assertEqual(result.status_code, 200, result.content)
        self.sign_in(self.student)
        row = self.browser.get(reverse('api:student-applications')).json()['results'][0]
        self.assertEqual((row['status'], row['company_message']), ('under_review', 'We received your application.'))
        self.assertEqual(Application.objects.filter(job=job).count(), 1)
        self.sign_in(self.employer)
        self.assertEqual(self.post('company-job-save', payload | {'title': 'Updated role'}, job.pk).status_code, 200)
        job.refresh_from_db()
        self.assertEqual((job.title, job.approval_status), ('Updated role', 'pending'))
        self.assertEqual(self.post('company-job-close', {}, job.pk).status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.approval_status, 'closed')

    def test_forum_posts_editing_and_acceptance(self):
        self.sign_in(self.student)
        response = self.post('question-create', {'title': 'Advice?', 'body': 'How should I prepare?'})
        self.assertEqual(response.status_code, 201, response.content)
        question_id = response.json()['id']
        self.sign_in(self.employer)
        self.assertEqual(self.post('question-save', {'title': 'Other', 'body': 'Other'}, question_id).status_code, 404)
        response = self.post('answer-create', {'body': 'Practice your introduction.'}, question_id)
        self.assertEqual(response.status_code, 201, response.content)
        answer_id = response.json()['id']
        self.assertEqual(self.post('answer-save', {'body': 'Practice a short introduction.'}, answer_id).status_code, 200)
        self.assertEqual(self.post('answer-accept', {}, answer_id).status_code, 404)
        self.sign_in(self.student)
        self.assertEqual(self.post('answer-accept', {}, answer_id).status_code, 200)
        self.assertTrue(Answer.objects.get(pk=answer_id).is_accepted)
        self.assertTrue(Question.objects.filter(pk=question_id, author=self.student).exists())
