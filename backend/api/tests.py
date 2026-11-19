from datetime import timedelta
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import StudentProfile, User
from applications.models import Application
from companies.models import Company
from forum.models import Answer, Question
from jobs.models import Job, Skill


class ReadApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user('student', email='student@example.test', role=User.Role.STUDENT)
        cls.other = User.objects.create_user('other', email='other@example.test', role=User.Role.STUDENT)
        cls.profile = StudentProfile.objects.create(user=cls.student, full_name='Test Student')
        cls.other_profile = StudentProfile.objects.create(user=cls.other, full_name='Other Student')
        cls.company = cls.make_company('company')
        cls.other_company = cls.make_company('other_company')
        cls.pending_company = cls.make_company('pending_company', Company.ApprovalStatus.PENDING)
        cls.job = cls.make_job(cls.company, 'Part-time developer', job_type=Job.JobType.PART_TIME)
        cls.other_job = cls.make_job(cls.other_company, 'Internship')
        cls.pending = cls.make_job(cls.company, 'Pending job', approval_status=Job.ApprovalStatus.PENDING)
        cls.closed = cls.make_job(cls.company, 'Closed job', approval_status=Job.ApprovalStatus.CLOSED)
        cls.expired = cls.make_job(cls.company, 'Expired job', deadline=timezone.localdate() - timedelta(days=1))
        cls.unapproved_company_job = cls.make_job(cls.pending_company, 'Job without approved company')
        cls.skill = Skill.objects.create(name='Django')
        cls.job.skills.add(cls.skill)
        cls.application = Application.objects.create(student=cls.profile, job=cls.job)
        cls.other_application = Application.objects.create(student=cls.other_profile, job=cls.other_job)
        cls.question = Question.objects.create(author=cls.student, title='Visible question', body='Body')
        cls.hidden_question = Question.objects.create(author=cls.other, title='Hidden question', body='Body', is_visible=False)
        cls.answer = Answer.objects.create(question=cls.question, author=cls.other, body='Visible answer')
        Answer.objects.create(question=cls.question, author=cls.other, body='Hidden answer', is_visible=False)

    @staticmethod
    def make_company(username, status=Company.ApprovalStatus.APPROVED):
        user = User.objects.create_user(username, email=f'{username}@example.test', role=User.Role.COMPANY)
        return Company.objects.create(user=user, company_name=username, approval_status=status)

    @staticmethod
    def make_job(company, title, **overrides):
        fields = {'deadline': timezone.localdate() + timedelta(days=3),
                  'approval_status': Job.ApprovalStatus.APPROVED,
                  'job_type': Job.JobType.INTERNSHIP, 'work_mode': Job.WorkMode.REMOTE}
        return Job.objects.create(company=company, title=title, **(fields | overrides))

    def read(self, name, *args, **params):
        return self.client.get(reverse(f'api:{name}', args=args), params)

    def test_public_jobs_only_include_open_approved_listings(self):
        result = self.read('job-list').json()['results']
        self.assertEqual({row['id'] for row in result}, {self.job.pk, self.other_job.pk})
        for job in [self.pending, self.closed, self.expired, self.unapproved_company_job]:
            self.assertEqual(self.read('job-detail', job.pk).status_code, 404)

    def test_job_filters_and_options(self):
        for filters in [{'job_type': 'part_time'}, {'skill': self.skill.pk}, {'keyword': 'Django'}]:
            self.assertEqual([row['id'] for row in self.read('job-list', **filters).json()['results']], [self.job.pk])
        self.assertEqual(self.read('job-list', skill='invalid').status_code, 400)
        self.assertEqual(self.read('options').json()['skills'][0]['name'], 'Django')

    def test_public_forum_excludes_hidden_posts_and_answers(self):
        self.assertEqual([row['id'] for row in self.read('question-list').json()['results']], [self.question.pk])
        detail = self.read('question-detail', self.question.pk).json()
        self.assertEqual(detail['answer_count'], 1)
        self.assertEqual([row['id'] for row in detail['answers']], [self.answer.pk])
        self.assertEqual(self.read('question-detail', self.hidden_question.pk).status_code, 404)

    def test_student_reads_only_their_profile_and_applications(self):
        self.assertEqual(self.read('student-profile').status_code, 403)
        self.assertFalse(self.read('session').json()['authenticated'])
        self.client.force_login(self.student)
        self.assertEqual(self.read('session').json()['user']['role'], 'student')
        self.assertEqual(self.read('student-profile').json()['profile']['full_name'], 'Test Student')
        self.assertEqual(self.read('company-profile').status_code, 403)
        self.assertEqual([row['id'] for row in self.read('student-applications').json()['results']], [self.application.pk])
        self.assertTrue(self.read('job-detail', self.job.pk).json()['already_applied'])
        self.assertFalse(self.read('job-detail', self.other_job.pk).json()['already_applied'])

    def test_applicant_can_view_closed_job_without_reopening_it(self):
        Job.objects.filter(pk=self.job.pk).update(
            approval_status=Job.ApprovalStatus.CLOSED, description='Build the frontend.',
        )
        self.client.force_login(self.student)
        application = self.read('student-applications').json()['results'][0]
        self.assertEqual(application['status'], 'applied')
        self.assertEqual(application['listing_status'], 'closed')
        self.assertEqual(self.read('job-detail', self.job.pk).status_code, 404)
        self.assertNotIn(self.job.pk, [row['id'] for row in self.read('job-list').json()['results']])
        response = self.read('student-application-job', self.application.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['description'], 'Build the frontend.')
        self.assertTrue(response.json()['details_available'])
        self.assertEqual(response.json()['listing_status'], 'closed')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.post(reverse('api:student-application-job', args=[self.application.pk])).status_code, 405)

    def test_application_job_details_are_private_to_the_applicant(self):
        self.assertEqual(self.read('student-application-job', self.application.pk).status_code, 403)
        self.client.force_login(self.other)
        self.assertEqual(self.read('student-application-job', self.application.pk).status_code, 404)
        self.client.force_login(self.company.user)
        self.assertEqual(self.read('student-application-job', self.application.pk).status_code, 403)

    def test_application_job_hides_unavailable_listing_description(self):
        Job.objects.filter(pk=self.job.pk).update(
            approval_status=Job.ApprovalStatus.PENDING, description='Unapproved draft',
        )
        self.client.force_login(self.student)
        detail = self.read('student-application-job', self.application.pk).json()
        self.assertEqual(detail['listing_status'], 'unavailable')
        self.assertFalse(detail['details_available'])
        self.assertNotIn('description', detail)

    def test_company_reads_only_its_own_jobs_and_applicants(self):
        self.client.force_login(self.company.user)
        self.assertEqual(self.read('company-profile').json()['profile']['company_name'], self.company.company_name)
        self.assertEqual(self.read('company-jobs').json()['count'], 4)
        self.assertEqual(self.read('company-job', self.other_job.pk).status_code, 404)
        self.assertEqual(self.read('job-applicants', self.other_job.pk).status_code, 404)
        self.assertEqual(self.read('application-review', self.other_application.pk).status_code, 404)
        self.assertEqual(self.read('job-applicants', self.job.pk).json()['results'][0]['id'], self.application.pk)

    def test_cv_download_requires_company_ownership(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            content = b'%PDF-test document'
            self.profile.cv = SimpleUploadedFile('test.pdf', content, content_type='application/pdf')
            self.profile.save()
            self.client.force_login(self.other_company.user)
            self.assertEqual(self.read('applicant-cv', self.application.pk).status_code, 404)
            self.client.force_login(self.company.user)
            review = self.read('application-review', self.application.pk).json()
            response = self.client.get(review['cv_url'])
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), content)
            response.close()
