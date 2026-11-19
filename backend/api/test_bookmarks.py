from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from applications.models import Application
from companies.models import Company
from jobs.models import Job, JobBookmark


class JobBookmarkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(username='bookmark_student', email='student@example.test', role=User.Role.STUDENT)
        cls.other = User.objects.create_user(username='other_student', email='other@example.test', role=User.Role.STUDENT)
        cls.employer = User.objects.create_user(username='bookmark_employer', email='employer@example.test', role=User.Role.COMPANY)
        cls.company = Company.objects.create(user=cls.employer, company_name='Example Company', approval_status='approved')
        cls.job = Job.objects.create(company=cls.company, title='Internship', job_type='internship',
                                     work_mode='remote', deadline=timezone.localdate() + timedelta(days=7),
                                     approval_status='approved')

    def url(self, name, *args):
        return reverse(f'api:{name}', args=args)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def mutate(self, action, data=None):
        self.client.get(self.url('csrf'))
        return self.client.post(self.url(f'bookmark-{action}', self.job.pk), data or {},
                                HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value)

    def test_student_saves_and_removes_without_applying(self):
        self.client.force_login(self.student)
        self.assertFalse(self.client.get(self.url('job-list')).json()['results'][0]['bookmarked'])
        for _ in range(2):
            self.assertEqual(self.mutate('save').json(), {'bookmarked': True})
        self.assertEqual(JobBookmark.objects.count(), 1)
        self.assertFalse(Application.objects.exists())
        self.assertTrue(self.client.get(self.url('job-list')).json()['results'][0]['bookmarked'])
        self.assertTrue(self.client.get(self.url('job-detail', self.job.pk)).json()['bookmarked'])
        saved = self.client.get(self.url('saved-jobs')).json()['results'][0]
        self.assertTrue(saved['available'])
        self.assertEqual(saved['id'], self.job.pk)
        self.assertEqual(self.mutate('remove').json(), {'bookmarked': False})
        self.assertEqual(self.client.get(self.url('saved-jobs')).json()['count'], 0)

    def test_bookmarks_are_private_and_student_only(self):
        self.assertEqual(self.mutate('save').status_code, 403)
        self.client.force_login(self.employer)
        self.assertEqual(self.mutate('save').status_code, 403)
        self.assertEqual(self.client.get(self.url('saved-jobs')).status_code, 403)
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(self.url('bookmark-save', self.job.pk)).status_code, 403)
        self.assertEqual(self.mutate('save', {'student': self.other.pk}).status_code, 200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url('saved-jobs')).json()['count'], 0)
        self.assertFalse(self.client.get(self.url('job-detail', self.job.pk)).json()['bookmarked'])
        self.assertEqual(self.mutate('remove', {'student': self.student.pk}).status_code, 200)
        self.assertTrue(JobBookmark.objects.filter(student=self.student, job=self.job).exists())

    def test_closed_job_is_unavailable_and_draft_edits_are_not_exposed(self):
        self.client.force_login(self.student)
        self.assertEqual(self.mutate('save').status_code, 200)
        Job.objects.filter(pk=self.job.pk).update(approval_status='closed', title='Private revised title')
        self.assertEqual(self.mutate('save').status_code, 404)
        saved = self.client.get(self.url('saved-jobs')).json()['results'][0]
        self.assertEqual(saved, {'id': self.job.pk, 'title': 'Internship', 'available': False, 'bookmarked': True})
        self.assertEqual(self.mutate('remove').status_code, 200)
        self.assertFalse(JobBookmark.objects.exists())

    def test_expired_jobs_and_unapproved_companies_cannot_be_saved(self):
        self.client.force_login(self.student)
        Job.objects.filter(pk=self.job.pk).update(deadline=timezone.localdate() - timedelta(days=1))
        self.assertEqual(self.mutate('save').status_code, 404)
        Job.objects.filter(pk=self.job.pk).update(deadline=timezone.localdate())
        Company.objects.filter(pk=self.company.pk).update(approval_status='pending')
        self.assertEqual(self.mutate('save').status_code, 404)
