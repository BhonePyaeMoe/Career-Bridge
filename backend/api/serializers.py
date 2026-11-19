from hashlib import sha256

from django.urls import reverse
from rest_framework import serializers

from accounts.models import StudentProfile
from applications.models import Application
from companies.models import Company
from forum.models import Answer, Question
from jobs.models import Job, Skill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name')
    skills = SkillSerializer(many=True)

    class Meta:
        model = Job
        fields = ('id', 'title', 'company_name', 'job_type', 'work_mode', 'location',
                  'deadline', 'skills', 'created_at')


class PublicJobSerializer(JobSerializer):
    bookmarked = serializers.BooleanField()

    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ('bookmarked',)


class SavedJobSerializer(JobSerializer):
    def to_representation(self, job):
        if not job.available:
            # Do not expose new edits to a listing that is no longer public.
            return {'id': job.pk, 'title': job.saved_title, 'available': False, 'bookmarked': True}
        return {**super().to_representation(job), 'available': True, 'bookmarked': True}


class PublicJobDetailSerializer(PublicJobSerializer):
    already_applied = serializers.BooleanField()

    class Meta(PublicJobSerializer.Meta):
        fields = PublicJobSerializer.Meta.fields + ('description', 'requirements', 'already_applied')


class CompanyJobSerializer(JobSerializer):
    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ('description', 'requirements', 'approval_status')


class ProfilePictureSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()

    def get_profile_picture_url(self, obj):
        if not obj.profile_picture or not obj.profile_picture.name.endswith('.webp'):
            return None
        version = sha256(obj.profile_picture.name.encode()).hexdigest()[:16]
        return f"{reverse('api:own-profile-picture')}?v={version}"


class StudentProfileSerializer(ProfilePictureSerializer):
    skills = SkillSerializer(many=True)
    has_cv = serializers.SerializerMethodField()

    def get_has_cv(self, obj):
        return bool(obj.cv)

    class Meta:
        model = StudentProfile
        fields = ('full_name', 'university', 'degree', 'phone', 'bio', 'skills', 'has_cv', 'profile_picture_url')


class CompanyProfileSerializer(ProfilePictureSerializer):
    class Meta:
        model = Company
        fields = ('company_name', 'industry', 'website', 'phone', 'description', 'address',
                  'approval_status', 'profile_picture_url')


class ApplicationSerializer(serializers.ModelSerializer):
    job_id = serializers.IntegerField()
    job_title = serializers.CharField(source='job.title')
    company_name = serializers.CharField(source='job.company.company_name')

    class Meta:
        model = Application
        fields = ('id', 'job_id', 'job_title', 'company_name', 'status', 'applied_at',
                  'updated_at', 'company_message', 'interview_datetime', 'interview_location')


def application_listing_status(job):
    if job.approval_status == Job.ApprovalStatus.CLOSED:
        return 'closed'
    if job.approval_status != Job.ApprovalStatus.APPROVED or not job.company.is_approved:
        return 'unavailable'
    return 'open' if job.is_open else 'expired'


class StudentApplicationSerializer(ApplicationSerializer):
    listing_status = serializers.SerializerMethodField()

    def get_listing_status(self, application):
        return application_listing_status(application.job)

    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ('listing_status',)


class ApplicantSerializer(ApplicationSerializer):
    full_name = serializers.CharField(source='student.full_name')
    university = serializers.CharField(source='student.university')
    degree = serializers.CharField(source='student.degree')
    cv_url = serializers.SerializerMethodField()

    def get_cv_url(self, obj):
        return reverse('api:applicant-cv', args=[obj.pk]) if obj.student.cv else None

    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ('full_name', 'university', 'degree',
                                                       'cover_message', 'cv_url')


class AnswerSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username')

    class Meta:
        model = Answer
        fields = ('id', 'author', 'body', 'is_accepted', 'created_at')


class QuestionSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username')
    answer_count = serializers.IntegerField()

    class Meta:
        model = Question
        fields = ('id', 'author', 'title', 'body', 'answer_count', 'created_at')


class QuestionDetailSerializer(QuestionSerializer):
    answers = AnswerSerializer(source='visible_answers', many=True)

    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + ('answers',)
